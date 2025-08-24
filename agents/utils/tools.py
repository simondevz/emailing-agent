import json
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError

class PlaywrightExecutor:
    def __init__(self, provider: str = "gmail", headless: bool = False):
        self.provider = provider
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_file = Path("sessions") / f"{provider}_auth.json"
        self.provider_config = {
            "gmail": {"url": "https://mail.google.com", "compose_selector": "[aria-label='Compose']"},
            "outlook": {"url": "https://outlook.live.com/mail/0/", "compose_selector": "[aria-label='New message']"}
        }
        self.headless = headless
        self.playwright = None

    async def setup(self) -> bool:
        """Initialize browser and load session with better error handling"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                timeout=30000
            )
            
            context_options = {
                'ignore_https_errors': True,
                'bypass_csp': True
            }
            
            if self.session_file.exists():
                try:
                    with open(self.session_file, 'r') as f:
                        storage_state = json.load(f)
                    if not isinstance(storage_state, dict) or 'cookies' not in storage_state:
                        raise ValueError("Invalid storage state format")
                    context_options['storage_state'] = storage_state
                    print(f"Loaded valid session from {self.session_file}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Invalid session file: {e}. Deleting and proceeding without.")
                    self.session_file.unlink()
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            config = self.provider_config.get(self.provider, self.provider_config["gmail"])
            print(f"Navigating to {config['url']} for provider {self.provider}")
            await self.page.goto(config["url"], timeout=60000)
            
            # Wait for Outlook UI to be fully loaded
            try:
                await self.page.wait_for_load_state('networkidle', timeout=60000)
                # Wait for key UI element (e.g., New message button or main content)
                await self.page.wait_for_selector(
                    config["compose_selector"],
                    state="visible",
                    timeout=30000
                )
                print(f"UI element {config['compose_selector']} is visible")
            except TimeoutError:
                print(f"Timeout waiting for {config['compose_selector']}. Taking screenshot for debugging.")
                Path("screenshots").mkdir(exist_ok=True)
                await self.page.screenshot(path=f"screenshots/{self.provider}_setup_failure.png")
                # Check if on login page
                current_url = self.page.url
                if "login.live.com" in current_url:
                    print(f"Detected login page: {current_url}. Session may be invalid.")
                    return False
            
            title = await self.page.title()
            if not title:
                raise RuntimeError("Page loaded but title is empty - possible initialization failure")
            
            print(f"Setup successful for {self.provider}. Page title: {title}")
            return True
        except TimeoutError as e:
            print(f"Timeout during setup for {self.provider}: {e}")
            return False
        except Exception as e:
            print(f"Setup failed for {self.provider}: {e}")
            return False

    async def cleanup(self):
        """Clean up browser and save session"""
        try:
            if self.context:
                storage_state = await self.context.storage_state()
                self.session_file.parent.mkdir(exist_ok=True)
                with open(self.session_file, 'w') as f:
                    json.dump(storage_state, f)
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup failed: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    async def get_dom(self) -> str:
        """Get simplified DOM for planner analysis"""
        if not self.page:
            print(f"Error: Page not initialized for {self.provider}")
            return "Error: Page not initialized"
        
        dom_js = """
        () => {
            const snapshot = {
                url: window.location.href,
                title: document.title,
                compose_open: false,
                clickable_elements: [],
                input_fields: [],
                buttons: []
            };
            
            // Check if compose is open
            const composeSelectors = [
                'div[role="dialog"]',
                '[aria-label*="compose" i], [aria-label*="new message" i]',
                '[data-testid*="compose"]'
            ];
            snapshot.compose_open = composeSelectors.some(sel => document.querySelector(sel));
            
            // Get clickable elements
            document.querySelectorAll('button, [role="button"], a, [data-tooltip], [aria-label]').forEach(el => {
                const text = el.textContent?.trim() || el.getAttribute('aria-label') || el.getAttribute('data-tooltip') || '';
                if (text.length > 0 && text.length < 100) {
                    snapshot.clickable_elements.push({
                        text: text,
                        tag: el.tagName.toLowerCase(),
                        selector: el.id ? `#${el.id}` : (el.className ? `.${el.className.split(' ')[0]}` : el.tagName.toLowerCase()),
                        visible: el.offsetParent !== null
                    });
                }
            });
            
            // Get input fields
            document.querySelectorAll('input, textarea, [contenteditable="true"], [role="textbox"]').forEach(el => {
                snapshot.input_fields.push({
                    type: el.type || 'text',
                    placeholder: el.placeholder || '',
                    aria_label: el.getAttribute('aria-label') || '',
                    name: el.name || '',
                    value: el.value || el.textContent || '',
                    selector: el.id ? `#${el.id}` : (el.name ? `[name="${el.name}"]` : (el.className ? `.${el.className.split(' ')[0]}` : el.tagName.toLowerCase())),
                    visible: el.offsetParent !== null
                });
            });
            
            // Get buttons with specific text
            ['Send', 'New message', 'Attach', 'To', 'Subject'].forEach(text => {
                const selector = `[aria-label*="${text}" i], [data-tooltip*="${text}" i], [title*="${text}" i]`;
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (!snapshot.buttons.some(b => b.text === text)) {
                        snapshot.buttons.push({
                            text: text,
                            selector: el.id ? `#${el.id}` : `[aria-label*="${text}" i]`,
                            available: el.offsetParent !== null
                        });
                    }
                });
            });
            
            return snapshot;
        }
        """
        
        try:
            result = await self.page.evaluate(dom_js)
            print(f"DOM captured successfully for {self.provider}")
            return json.dumps(result, indent=2)
        except Exception as e:
            print(f"DOM capture failed for {self.provider}: {str(e)}")
            Path("screenshots").mkdir(exist_ok=True)
            await self.page.screenshot(path=f"screenshots/{self.provider}_dom_failure.png")
            return f"DOM capture failed: {str(e)}"

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action based on planner instruction"""
        if not self.page:
            print(f"Error: Page not initialized for {self.provider}")
            return {"success": False, "error": "Page not initialized"}
        
        try:
            action_type = action.get("type", "")
            selector = action.get("selector", "")
            value = action.get("value", "")
            
            print(f"Executing action: {action_type} on {selector} with value '{value}'")
            
            if action_type == "click":
                await self.page.locator(selector).first.click(timeout=5000)
                await self.page.wait_for_timeout(1000)
                return {"success": True, "action": f"Clicked {selector}"}
            
            elif action_type == "fill":
                element = self.page.locator(selector).first
                await element.click(timeout=5000)
                await element.fill(value)
                return {"success": True, "action": f"Filled {selector} with {value}"}
            
            elif action_type == "type":
                element = self.page.locator(selector).first
                await element.click(timeout=5000)
                await element.type(value, delay=50)
                return {"success": True, "action": f"Typed {value} into {selector}"}
            
            elif action_type == "press":
                await self.page.keyboard.press(value)
                return {"success": True, "action": f"Pressed {value}"}
            
            elif action_type == "wait":
                await self.page.wait_for_timeout(int(value))
                return {"success": True, "action": f"Waited {value}ms"}
            
            elif action_type == "screenshot":
                path = f"screenshots/step_{action.get('step', 'current')}.png"
                Path("screenshots").mkdir(exist_ok=True)
                await self.page.screenshot(path=path)
                return {"success": True, "action": f"Screenshot saved to {path}"}
            
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            print(f"Action execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
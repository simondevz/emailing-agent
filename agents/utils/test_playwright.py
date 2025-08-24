import asyncio
from pathlib import Path
from agents.actions.playwright_execution import PlaywrightExecutor

async def test_setup(provider="outlook"):
    executor = PlaywrightExecutor(provider, headless=False)
    try:
        success = await executor.setup()
        print(f"Setup: {success}")
        if success:
            # Take a screenshot for debugging
            Path("screenshots").mkdir(exist_ok=True)
            await executor.page.screenshot(path=f"screenshots/{provider}_initial.png")
            print(f"Screenshot saved to screenshots/{provider}_initial.png")
            print(await executor.get_dom())
    finally:
        await executor.cleanup()

if __name__ == "__main__":
    asyncio.run(test_setup())
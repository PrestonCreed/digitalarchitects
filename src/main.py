import asyncio
import argparse
import sys
from pathlib import Path
from digitalarchitects.config.config_manager import ConfigManager
from digitalarchitects.utils.logging_config import LoggingManager
from digitalarchitects.core.MainArchitecture import DigitalArchitect

class DigitalArchitectsApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logging_manager = LoggingManager(self.config_manager)
        self.architect = None
        
    async def startup(self):
        """Initialize all components"""
        try:
            # Initialize Digital Architect
            self.architect = DigitalArchitect(self.config_manager)
            await self.architect.start()
            
            # Additional startup tasks...
            print("Digital Architects system initialized successfully!")
            
        except Exception as e:
            print(f"Failed to initialize system: {e}")
            sys.exit(1)
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        if self.architect:
            await self.architect.ws_manager.disconnect()
        print("\nShutdown complete.")
    
    async def run(self):
        """Main application loop"""
        await self.startup()
        
        try:
            while True:
                # Main application loop
                # This could handle:
                # - CLI commands
                # - Scheduled tasks
                # - System monitoring
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await self.shutdown()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Digital Architects System')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if args.debug:
        # Set debug configurations
        pass
        
    app = DigitalArchitectsApp()
    asyncio.run(app.run())

if __name__ == "__main__":
    main()
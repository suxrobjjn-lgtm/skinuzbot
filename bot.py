# Skenuz CS2 Bot & Mini App Runner
import asyncio
import skenuz_server

if __name__ == "__main__":
    try:
        asyncio.run(skenuz_server.main())
    except (KeyboardInterrupt, SystemExit):
        pass

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "false" if os.environ.get("RENDER") else "true").lower() == "true"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=reload)

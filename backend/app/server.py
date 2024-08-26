from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from app.agent import agent_chain, InputChat
from langchain_core.runnables import RunnableLambda
app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")



# Edit this to add the chain you want to add
add_routes(
    app,
    RunnableLambda(agent_chain).with_types(input_type=InputChat),
    path="/agent",
    playground_type="chat",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio
import logging 
from src.graphs.simple_graph import create_simple_graph
from src.state.schemas import create_initial_state
import json 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_simple_flow(): 
  print('=' * 60)
  print('Testing simple flow')
  print('=' * 60)

  graph = create_simple_graph()

  print("\n--- Test 1: Simple Task ---")
  initial_state = create_initial_state(
    task='Write a merge sort in Dart', 
    technique='lead-and-reveal'
  )
  print(f"Initial state: {json.dumps(initial_state, indent=2)}")
  final_state = await graph.ainvoke(initial_state) 
  # Note: doing final_state = graph.ainvoke(inital_state) would only ret the coroutine 
  # await keyword must be used 

  print(f"\nFinal state completed: {final_state['completed']}")
  print(f"Code generated: {bool(final_state.get('code_solution'))}")
  print(f"Steps created: {final_state.get('total_steps', 0)}")
  print(f"Messages: {len(final_state.get('messages', []))}")
  if final_state.get('code_solution'):
    print("\nGenerated code:")
    print("-" * 40)
    print(final_state['code_solution'])
    print("-" * 40)

async def test_graph_streaming(): 
    print("\n" + "=" * 60)
    print("Testing Streaming Execution")
    print("=" * 60)

    graph = create_simple_graph()

    initial_state = create_initial_state(
        task="Write a bubble sort function in C",
        technique="baseline"
    )

    print("\nStreaming state updates:")
    async for event in graph.astream(initial_state): 
       for node, update in event.items(): 
          print(f"\nNode '{node}' update:")
          for key, value in update.items(): 
             if key != 'messages': 
                print(f"  {key}: {str(value)[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_simple_flow())
    asyncio.run(test_graph_streaming())

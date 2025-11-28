"""Compare GPT-5 model variants for computer use tasks."""
import requests
import urllib3
import time
import base64
from io import BytesIO
urllib3.disable_warnings()

import pyautogui

# Take screenshot
print("Taking screenshot...")
screenshot = pyautogui.screenshot()
screenshot = screenshot.resize((960, 540))
buffer = BytesIO()
screenshot.save(buffer, format='JPEG', quality=70)
img_b64 = base64.b64encode(buffer.getvalue()).decode()

API_KEY = '9f3680b1c04548a0a0ef5b0eb65d8764'
BASE_URL = 'https://spd-dev-openai-std-apim.azure-api.us/openai/v1'
headers = {'api-key': API_KEY, 'Content-Type': 'application/json'}

print('='*70)
print('MODEL COMPARISON - Vision + Tool Calling')
print('='*70)

tools = [{
    'type': 'function',
    'function': {
        'name': 'click',
        'description': 'Click at x,y coordinates on the screen',
        'parameters': {
            'type': 'object',
            'properties': {
                'x': {'type': 'integer', 'description': 'X coordinate'},
                'y': {'type': 'integer', 'description': 'Y coordinate'}
            },
            'required': ['x', 'y']
        }
    }
}]

system = 'You MUST use the click function. Look at the screenshot and click somewhere. Do NOT respond with text - only use the click tool.'

models = ['gpt-5-nano', 'gpt-5-mini', 'gpt-5', 'gpt-5.1']
results = {}

for model in models:
    print(f"\nTesting {model}...")
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': 'Use the click function now.'},
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}}
            ]}
        ],
        'tools': tools,
        'tool_choice': 'auto',
        'max_completion_tokens': 256
    }
    
    start = time.time()
    r = requests.post(f'{BASE_URL}/responses', json=payload, headers=headers, verify=False, timeout=60)
    elapsed = time.time() - start
    
    if r.status_code == 200:
        data = r.json()
        msg = data['choices'][0]['message']
        tool_calls = msg.get('tool_calls', [])
        
        if tool_calls:
            results[model] = {'time': elapsed, 'success': True, 'args': tool_calls[0]['function']['arguments']}
        else:
            results[model] = {'time': elapsed, 'success': False, 'reason': 'No tool call'}
    else:
        results[model] = {'time': elapsed, 'success': False, 'error': r.status_code}

print()
print('='*70)
print('RESULTS')
print('='*70)
print(f"{'Model':<15} {'Time':<10} {'Status':<8} {'Result'}")
print('-'*70)
for model, r in results.items():
    status = '✅' if r.get('success') else '❌'
    time_str = f"{r['time']:.1f}s"
    if r.get('success'):
        result = r.get('args', '')
    else:
        result = r.get('reason', r.get('error', 'Failed'))
    print(f"{model:<15} {time_str:<10} {status:<8} {result}")

# Winner
winners = [(m, r) for m, r in results.items() if r.get('success')]
if winners:
    fastest = min(winners, key=lambda x: x[1]['time'])
    print()
    print(f"🏆 FASTEST WITH TOOL CALLING: {fastest[0]} ({fastest[1]['time']:.1f}s)")
print('='*70)

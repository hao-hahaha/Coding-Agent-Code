// SPDX-License-Identifier: Apache-2.0
let localModel;
let useGpu = true;

try {
  const saved = localStorage.getItem('USE_GPU');
  if (saved !== null) {
    useGpu = saved !== '0';
  }
} catch {}

export function setUseGpu(flag) {
  useGpu = !!flag;
  try {
    localStorage.setItem('USE_GPU', useGpu ? '1' : '0');
  } catch {}
  localModel = null;
}

export function gpuBackend() {
  return useGpu && typeof navigator !== 'undefined' && navigator.gpu
    ? 'webgpu'
    : 'wasm-simd';
}

async function loadLocal() {
  if (!localModel) {
    try {
      const { pipeline } = await import('../lib/bundle.esm.min.js');
      const backend = gpuBackend();
      if (typeof window !== 'undefined') {
        window.LLM_BACKEND = backend;
      }
      if (window.GPT2_MODEL_BASE64) {
        const bytes = Uint8Array.from(atob(window.GPT2_MODEL_BASE64), c => c.charCodeAt(0));
        const blob = new Blob([bytes]);
        const url = URL.createObjectURL(blob);
        localModel = await pipeline('text-generation', url, { backend });
      } else {
        localModel = await pipeline('text-generation', './wasm_llm/', { backend });
      }
    } catch (err) {
      localModel = async (p) => `[offline] ${p}`;
    }
  }
  return localModel;
}

export async function chat(prompt) {
  const key = localStorage.getItem('OPENAI_API_KEY');
  if (key) {
    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    const data = await resp.json();
    return data.choices[0].message.content.trim();
  }
  const model = await loadLocal();
  const out = await model(prompt);
  return typeof out === 'string' ? out : out[0]?.generated_text?.trim();
}


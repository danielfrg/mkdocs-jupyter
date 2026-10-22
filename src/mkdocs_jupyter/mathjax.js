/* Shared by full pages and Material's instant navigation. */
(() => {
  const config = JSON.parse(document.currentScript.dataset.mkdocsJupyterMathjax);
  if (window.mkdocsJupyterMathJax) return;

  let loading;
  let queue = Promise.resolve();
  let previous = [];

  const ready = async () => {
    if (!loading) {
      loading = (async () => {
        let math = window.MathJax;
        if (!math?.typesetPromise) {
          const url = new URL(config.url, document.baseURI).href;
          const existing = Array.from(document.scripts).find(script =>
            script.src && (script.src === url || script.id === 'MathJax-script' ||
              (/mathjax/i.test(script.src) &&
               /\/(?:MathJax|latest|(?:tex|mml)(?:-mml)?-(?:chtml|svg))\.js(?:[?#]|$)/i.test(script.src))));
          if (existing) {
            if (!math?.startup?.promise) {
              await new Promise((resolve, reject) => {
                existing.addEventListener('load', resolve, { once: true });
                existing.addEventListener('error', reject, { once: true });
              });
            }
          } else {
            // Keep site macros, delimiters and startup hooks when supplied.
            const options = math || {};
            window.MathJax = {
              ...options,
              loader: {
                ...options.loader,
                load: Array.from(new Set(['ui/safe', ...(options.loader?.load || [])]))
              },
              startup: { typeset: false, ...options.startup },
              tex: {
                tags: 'ams',
                useLabelIds: true,
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                ...options.tex
              }
            };
            await new Promise((resolve, reject) => {
              const script = document.createElement('script');
              script.src = config.url;
              script.id = 'MathJax-script';
              script.async = true;
              script.onload = resolve;
              script.onerror = reject;
              document.head.appendChild(script);
            });
          }
        }
        math = window.MathJax;
        await math.startup.promise;
        return math;
      })();
    }
    const math = await loading;
    // A site owner can extend the v3 queue again on each navigation.
    await math.startup.promise;
    return math;
  };

  const unrendered = node => {
    if (node.matches('mjx-container')) return [];
    if (!node.querySelector('mjx-container')) return [node];
    // In v3, scanning generated assistive MathML again produces nested output.
    return Array.from(node.children).flatMap(unrendered);
  };

  const refresh = () => {
    // A separate chain also serializes v3, without changing v4's startup promise.
    queue = queue.then(async () => {
      const notebooks = Array.from(document.querySelectorAll('.jupyter-wrapper'));
      if (!notebooks.length && !previous.length) return;
      if (notebooks.length === previous.length &&
          notebooks.every((node, index) => node === previous[index])) return;
      const math = await ready();
      if (previous.length) {
        math.typesetClear(previous);
        math.texReset();
      }
      previous = notebooks.filter(node => node.isConnected);
      const pending = previous.flatMap(unrendered);
      if (pending.length) await math.typesetPromise(pending);
    }).catch(error => console.error('mkdocs-jupyter: MathJax rendering failed', error));
    return queue;
  };

  window.mkdocsJupyterMathJax = { refresh };
  const start = () => {
    if (typeof document$ !== 'undefined') document$.subscribe(refresh);
    else refresh();
  };
  // Theme bundles and user-provided MathJax scripts can follow notebook content.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else start();
})();

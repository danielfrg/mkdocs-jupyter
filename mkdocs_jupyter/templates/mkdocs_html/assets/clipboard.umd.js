(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global = global || self, global.ClipboardCopyElement = factory());
  }(this, function () { 'use strict';

    function createNode(text) {
      const node = document.createElement('pre');
      node.style.width = '1px';
      node.style.height = '1px';
      node.style.position = 'fixed';
      node.style.top = '5px';
      node.textContent = text;
      return node;
    }

    function copyNode(node) {
      if ('clipboard' in navigator) {
        // eslint-disable-next-line flowtype/no-flow-fix-me-comments
        // $FlowFixMe Clipboard is not defined in Flow yet.
        return navigator.clipboard.writeText(node.textContent);
      }

      const selection = getSelection();

      if (selection == null) {
        return Promise.reject(new Error());
      }

      selection.removeAllRanges();
      const range = document.createRange();
      range.selectNodeContents(node);
      selection.addRange(range);
      document.execCommand('copy');
      selection.removeAllRanges();
      return Promise.resolve();
    }
    function copyText(text) {
      if ('clipboard' in navigator) {
        // eslint-disable-next-line flowtype/no-flow-fix-me-comments
        // $FlowFixMe Clipboard is not defined in Flow yet.
        return navigator.clipboard.writeText(text);
      }

      const body = document.body;

      if (!body) {
        return Promise.reject(new Error());
      }

      const node = createNode(text);
      body.appendChild(node);
      copyNode(node);
      body.removeChild(node);
      return Promise.resolve();
    }

    function copy(button) {
      const id = button.getAttribute('for');
      const text = button.getAttribute('value');

      function trigger() {
        button.dispatchEvent(new CustomEvent('clipboard-copy', {
          bubbles: true
        }));
      }

      if (text) {
        copyText(text).then(trigger);
      } else if (id) {
        const root = 'getRootNode' in Element.prototype ? button.getRootNode() : button.ownerDocument;
        if (!(root instanceof Document || 'ShadowRoot' in window && root instanceof ShadowRoot)) return;
        const node = root.getElementById(id);
        if (node) copyTarget(node).then(trigger);
      }
    }

    function copyTarget(content) {
      if (content instanceof HTMLInputElement || content instanceof HTMLTextAreaElement) {
        return copyText(content.value);
      } else if (content instanceof HTMLAnchorElement && content.hasAttribute('href')) {
        return copyText(content.href);
      } else {
        return copyNode(content);
      }
    }

    function clicked(event) {
      const button = event.currentTarget;

      if (button instanceof HTMLElement) {
        copy(button);
      }
    }

    function keydown(event) {
      if (event.key === ' ' || event.key === 'Enter') {
        const button = event.currentTarget;

        if (button instanceof HTMLElement) {
          event.preventDefault();
          copy(button);
        }
      }
    }

    function focused(event) {
      event.currentTarget.addEventListener('keydown', keydown);
    }

    function blurred(event) {
      event.currentTarget.removeEventListener('keydown', keydown);
    }

    class ClipboardCopyElement extends HTMLElement {
      constructor() {
        super();
        this.addEventListener('click', clicked);
        this.addEventListener('focus', focused);
        this.addEventListener('blur', blurred);
      }

      connectedCallback() {
        if (!this.hasAttribute('tabindex')) {
          this.setAttribute('tabindex', '0');
        }

        if (!this.hasAttribute('role')) {
          this.setAttribute('role', 'button');
        }
      }

      get value() {
        return this.getAttribute('value') || '';
      }

      set value(text) {
        this.setAttribute('value', text);
      }

    }

    if (!window.customElements.get('clipboard-copy')) {
      window.ClipboardCopyElement = ClipboardCopyElement;
      window.customElements.define('clipboard-copy', ClipboardCopyElement);
    }

    return ClipboardCopyElement;

  }));

(() => {
  'use strict';

  const registrationLabels = {
    institution_type: 'Tipo de entidad',
    country: 'País',
    language: 'Idioma preferido para el intercambio'
  };
  const pickers = new Map();
  let nextId = 0;

  function labelFor(select) {
    const id = select.getAttribute('aria-labelledby');
    const label = id && document.getElementById(id);
    return label?.textContent.trim() ||
      (select.id === 'section-select' ? document.querySelector('label[for="section-select"]')?.textContent.trim() : '') ||
      registrationLabels[select.name] || '';
  }

  function makePicker(select) {
    const id = `azfa-select-${nextId++}`;
    const wrapper = document.createElement('div');
    wrapper.className = 'country-picker';
    select.before(wrapper);
    wrapper.append(select);
    // The native select retains its form value, validation, and fallback behavior.
    select.classList.add('country-native');
    select.tabIndex = -1;
    select.setAttribute('aria-hidden', 'true');

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'country-trigger';
    trigger.setAttribute('data-no-translate', '');
    trigger.setAttribute('role', 'combobox');
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', `${id}-options`);
    trigger.setAttribute('aria-required', String(select.required));
    const value = document.createElement('span');
    trigger.append(value);

    const list = document.createElement('div');
    list.id = `${id}-options`;
    list.className = 'country-options';
    list.setAttribute('data-no-translate', '');
    list.setAttribute('role', 'listbox');
    list.hidden = true;
    wrapper.append(trigger, list);

    let choices = [], signature = '', active = 0, search = '', timer;
    function close() {
      list.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      trigger.removeAttribute('aria-activedescendant');
    }
    function sync() {
      const chosen = select.selectedOptions[0];
      const text = chosen?.textContent || '';
      if (value.textContent !== text) value.textContent = text;
      [...list.children].forEach((item, i) =>
        item.setAttribute('aria-selected', String(choices[i].value === select.value)));
    }
    function refresh() {
      const label = labelFor(select);
      trigger.setAttribute('aria-label', label);
      list.setAttribute('aria-label', label);
      const options = [...select.options];
      const next = JSON.stringify(options.map(option => [option.value, option.textContent]));
      if (next !== signature) {
        signature = next;
        choices = options;
        list.replaceChildren(...options.map((option, i) => {
          const item = document.createElement('div');
          item.id = `${id}-option-${i}`;
          item.setAttribute('role', 'option');
          item.textContent = option.textContent;
          return item;
        }));
        close();
      }
      sync();
    }
    function highlight(i) {
      if (!choices.length) return;
      active = (i + choices.length) % choices.length;
      [...list.children].forEach((item, n) => item.classList.toggle('highlighted', n === active));
      trigger.setAttribute('aria-activedescendant', list.children[active].id);
      list.children[active].scrollIntoView({block: 'nearest'});
    }
    function open() {
      refresh();
      if (!choices.length) return;
      list.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      highlight(Math.max(0, choices.findIndex(option => option.value === select.value)));
    }
    function choose(i) {
      if (!choices[i]) return;
      select.value = choices[i].value;
      select.dispatchEvent(new Event('change', {bubbles: true}));
      refresh();
      close();
      trigger.focus();
    }

    trigger.addEventListener('click', () => list.hidden ? open() : close());
    trigger.addEventListener('keydown', event => {
      if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' '].includes(event.key)) {
        event.preventDefault();
        if (list.hidden) { open(); return; }
        if (event.key === 'Enter' || event.key === ' ') choose(active);
        else highlight(event.key === 'Home' ? 0 : event.key === 'End' ? choices.length - 1 : active + (event.key === 'ArrowDown' ? 1 : -1));
      } else if (event.key === 'Escape') { event.preventDefault(); close(); }
      else if (event.key === 'Tab') close();
      else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
        clearTimeout(timer);
        search += event.key.toLocaleLowerCase();
        if (list.hidden) open();
        const i = choices.findIndex(option => option.textContent.toLocaleLowerCase().startsWith(search));
        if (i >= 0) highlight(i);
        timer = setTimeout(() => search = '', 650);
      }
    });
    list.addEventListener('mousedown', event => event.preventDefault());
    list.addEventListener('click', event => {
      const item = event.target.closest('[role="option"]');
      if (item && list.contains(item)) choose([...list.children].indexOf(item));
    });
    document.addEventListener('click', event => { if (!wrapper.contains(event.target)) close(); });
    select.addEventListener('change', refresh);
    select.addEventListener('invalid', event => { event.preventDefault(); trigger.focus(); open(); });
    select.form?.addEventListener('reset', () => setTimeout(() => { refresh(); close(); }, 0));
    refresh();
    return refresh;
  }

  function refreshAll() {
    document.querySelectorAll('select:not(.country-native)').forEach(select => {
      // Preserve canonical registration values when the displayed language changes.
      if (select.name && registrationLabels[select.name]) {
        for (const option of select.options) {
          if (!option.hasAttribute('value')) {
            const spanish = Object.keys(window.AZFA_EN || {}).find(key => window.AZFA_EN[key] === option.textContent);
            option.value = spanish || option.textContent;
          }
        }
      }
      pickers.set(select, makePicker(select));
    });
    for (const [select, refresh] of pickers) {
      if (select.isConnected) refresh();
      else pickers.delete(select);
    }
  }

  document.addEventListener('azfa:selects-updated', refreshAll);
  document.addEventListener('azfa:language-changed', refreshAll);
  refreshAll();
})();

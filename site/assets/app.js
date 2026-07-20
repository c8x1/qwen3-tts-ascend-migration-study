const VALID = new Set(['expanded', 'collapsed']);
const STORAGE_KEYS = {
  left: 'q3a.sidebar.left',
  right: 'q3a.sidebar.right',
};

export class SidebarController {
  constructor(documentRef = document, windowRef = window) {
    this.document = documentRef;
    this.window = windowRef;
    this.root = documentRef.documentElement;
    this.toggles = {
      left: documentRef.querySelector('#toggle-left'),
      right: documentRef.querySelector('#toggle-right'),
    };
    this.sidebars = {
      left: documentRef.querySelector('#chapter-nav'),
      right: documentRef.querySelector('#evidence-rail'),
    };
    this.backdrop = documentRef.querySelector('.drawer-backdrop');
    this.lastTrigger = null;
    this.memory = new Map();
    this.boundKeydown = (event) => this.onKeydown(event);
    this.boundResize = () => this.onResize();
  }

  mode() {
    if (this.window.innerWidth <= 720) return 'mobile';
    if (this.window.innerWidth < 1200) return 'laptop';
    return 'wide';
  }

  defaultState(side) {
    return this.mode() === 'laptop' && side === 'right' ? 'collapsed' : 'expanded';
  }

  read(side) {
    const memoryValue = this.memory.get(side);
    if (VALID.has(memoryValue)) return memoryValue;
    try {
      const value = this.window.localStorage.getItem(STORAGE_KEYS[side]);
      if (VALID.has(value)) return value;
      if (value !== null) this.window.localStorage.removeItem(STORAGE_KEYS[side]);
    } catch {}
    return this.defaultState(side);
  }

  write(side, value) {
    this.memory.set(side, value);
    try {
      this.window.localStorage.setItem(STORAGE_KEYS[side], value);
    } catch {
      // In-memory state remains available for this page view.
    }
  }

  apply(side, value) {
    this.root.dataset[`${side}Sidebar`] = value;
    this.syncToggle(side);
  }

  syncToggle(side) {
    const mobile = this.mode() === 'mobile';
    const expanded = mobile
      ? this.root.dataset.drawerOpen === side
      : this.root.dataset[`${side}Sidebar`] === 'expanded';
    const action = expanded ? (mobile ? '关闭' : '收起') : (mobile ? '打开' : '展开');
    this.toggles[side].setAttribute('aria-expanded', String(expanded));
    this.toggles[side].setAttribute('aria-label', `${action}${side === 'left' ? '章节导航' : '证据栏'}`);
  }

  syncToggles() {
    this.syncToggle('left');
    this.syncToggle('right');
  }

  toggle(side) {
    if (this.mode() === 'mobile') {
      if (this.root.dataset.drawerOpen === side) this.closeDrawer();
      else this.openDrawer(side, this.toggles[side]);
      return;
    }
    const current = this.root.dataset[`${side}Sidebar`];
    const next = current === 'expanded' ? 'collapsed' : 'expanded';
    this.write(side, next);
    this.apply(side, next);
  }

  openDrawer(side, trigger) {
    this.closeDrawer(false);
    this.lastTrigger = trigger;
    this.root.dataset.drawerOpen = side;
    this.backdrop.hidden = false;
    this.sidebars.left.inert = side !== 'left';
    this.sidebars.right.inert = side !== 'right';
    this.sidebars[side].setAttribute('role', 'dialog');
    this.sidebars[side].setAttribute('aria-modal', 'true');
    this.syncToggles();
    const target = this.sidebars[side].querySelector('a, button, input, [tabindex]:not([tabindex="-1"])');
    target?.focus();
  }

  closeDrawer(restoreFocus = true) {
    const side = this.root.dataset.drawerOpen;
    if (!side) {
      this.backdrop.hidden = true;
      this.syncToggles();
      return;
    }
    delete this.root.dataset.drawerOpen;
    this.backdrop.hidden = true;
    this.sidebars[side].removeAttribute('role');
    this.sidebars[side].removeAttribute('aria-modal');
    if (this.mode() === 'mobile') {
      this.sidebars.left.inert = true;
      this.sidebars.right.inert = true;
    }
    this.syncToggles();
    if (restoreFocus) this.lastTrigger?.focus();
  }

  trapFocus(event) {
    const side = this.root.dataset.drawerOpen;
    if (!side || event.key !== 'Tab') return;
    const focusable = [...this.sidebars[side].querySelectorAll('a, button, input, [tabindex]:not([tabindex="-1"])')]
      .filter((node) => !node.disabled && node.getClientRects().length > 0);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && this.document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && this.document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  onKeydown(event) {
    if (event.key === 'Escape') this.closeDrawer();
    if (event.altKey && event.key === '[') { event.preventDefault(); this.toggle('left'); }
    if (event.altKey && event.key === ']') { event.preventDefault(); this.toggle('right'); }
    this.trapFocus(event);
  }

  onResize() {
    if (this.mode() === 'mobile') {
      this.closeDrawer(false);
      this.sidebars.left.inert = true;
      this.sidebars.right.inert = true;
      this.syncToggles();
      return;
    }
    this.closeDrawer(false);
    this.sidebars.left.inert = false;
    this.sidebars.right.inert = false;
    this.sidebars.left.removeAttribute('role');
    this.sidebars.right.removeAttribute('role');
    this.sidebars.left.removeAttribute('aria-modal');
    this.sidebars.right.removeAttribute('aria-modal');
    this.apply('left', this.read('left'));
    this.apply('right', this.read('right'));
  }

  init() {
    this.root.classList.add('js');
    this.apply('left', this.read('left'));
    this.apply('right', this.read('right'));
    if (this.mode() === 'mobile') this.onResize();
    this.toggles.left.addEventListener('click', () => this.toggle('left'));
    this.toggles.right.addEventListener('click', () => this.toggle('right'));
    this.backdrop.addEventListener('click', () => this.closeDrawer());
    this.document.querySelectorAll('[data-close-drawer]').forEach((button) =>
      button.addEventListener('click', () => this.closeDrawer())
    );
    this.document.addEventListener('keydown', this.boundKeydown);
    this.window.addEventListener('resize', this.boundResize);
  }
}

class ChapterTreeController {
  constructor(documentRef = document) {
    this.document = documentRef;
    this.buttons = [...documentRef.querySelectorAll('.tree-toggle[aria-controls]')];
  }

  setExpanded(button, expanded) {
    const branch = this.document.getElementById(button.getAttribute('aria-controls'));
    if (!branch) return;
    button.setAttribute('aria-expanded', String(expanded));
    branch.hidden = !expanded;
  }

  init() {
    this.buttons.forEach((button) => {
      const branch = this.document.getElementById(button.getAttribute('aria-controls'));
      this.setExpanded(button, branch?.dataset.defaultExpanded === 'true');
      button.addEventListener('click', () => this.setExpanded(button, button.getAttribute('aria-expanded') !== 'true'));
    });

    let branch = this.document.querySelector('[aria-current="page"]')?.closest('.tree-branch');
    while (branch) {
      const button = this.document.querySelector(`[aria-controls="${branch.id}"]`);
      if (button) this.setExpanded(button, true);
      branch = branch.parentElement?.closest('.tree-branch');
    }
  }
}

export class SearchController {
  constructor(documentRef = document, windowRef = window) {
    this.document = documentRef;
    this.window = windowRef;
    this.root = documentRef.documentElement;
    this.button = documentRef.querySelector('.search-enhancement');
    this.form = documentRef.querySelector('#site-search');
    this.input = this.form?.querySelector('input[type="search"]');
    this.results = documentRef.querySelector('.search-results');
    this.resultsStatus = documentRef.querySelector('#search-results-status');
    const data = documentRef.querySelector('#search-data');
    this.data = null;
    if (data) {
      try {
        const parsed = JSON.parse(data.textContent);
        if (Array.isArray(parsed)) this.data = parsed;
      } catch {}
    }
  }

  close() {
    this.root.classList.remove('search-open');
    this.button?.setAttribute('aria-expanded', 'false');
    this.button?.setAttribute('aria-label', '打开站内搜索');
  }

  renderResults(query) {
    if (!this.results || !this.resultsStatus || !this.data) return;
    const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const matches = this.data
      .filter((item) => terms.every((term) => item.searchable.includes(term)))
      .slice(0, 100);
    this.results.replaceChildren(...matches.map((item) => {
      const link = this.document.createElement('a');
      link.href = item.href;
      link.textContent = `${item.title} · ${item.kind}`;
      return link;
    }));
    this.resultsStatus.textContent = terms.length ? `找到 ${matches.length} 条结果` : '请输入关键词';
  }

  init() {
    const query = new URLSearchParams(this.window.location.search).get('q') ?? '';
    if (this.input) this.input.value = query;
    this.renderResults(query);
    this.form?.addEventListener('submit', (event) => {
      if (!this.data || this.window.location.pathname.split('/').pop() !== 'search.html') return;
      event.preventDefault();
      const value = this.input?.value ?? '';
      const url = new URL(this.window.location.href);
      if (value.trim()) url.searchParams.set('q', value);
      else url.searchParams.delete('q');
      this.window.history.replaceState({}, '', url);
      this.renderResults(value);
    });
    this.button?.addEventListener('click', () => {
      const opening = !this.root.classList.contains('search-open');
      if (!opening) {
        this.close();
        return;
      }
      this.root.classList.add('search-open');
      this.button.setAttribute('aria-expanded', 'true');
      this.button.setAttribute('aria-label', '关闭站内搜索');
      this.input?.focus();
    });
    this.form?.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.close();
        this.button?.focus();
      }
    });
  }
}

class CopyController {
  constructor(documentRef = document, navigatorRef = navigator) {
    this.document = documentRef;
    this.navigator = navigatorRef;
  }

  async copy(text) {
    if (this.navigator.clipboard?.writeText) {
      try {
        await this.navigator.clipboard.writeText(text);
        return true;
      } catch {}
    }

    const textarea = this.document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    this.document.body.append(textarea);
    textarea.select();
    let copied = false;
    try { copied = this.document.execCommand('copy'); } catch {}
    textarea.remove();
    return copied;
  }

  init() {
    this.document.querySelectorAll('.copy-source[data-copy-target]').forEach((button) => {
      button.addEventListener('click', async () => {
        const source = this.document.getElementById(button.dataset.copyTarget);
        const status = button.parentElement?.querySelector('.copy-status');
        const copied = await this.copy(source?.textContent ?? '');
        if (status) status.textContent = copied ? '已复制' : '请手动复制';
      });
    });
  }
}

class EvidenceRailController {
  constructor(documentRef = document, sidebarController = null) {
    this.document = documentRef;
    this.root = documentRef.documentElement;
    this.rail = documentRef.querySelector('#evidence-rail');
    this.toggle = documentRef.querySelector('#toggle-right');
    this.sidebarController = sidebarController;
    this.observer = null;
  }

  isMeaningful(node) {
    if (!node.textContent.trim()) return false;
    if (!node.matches('a')) return true;
    return Boolean(node.getAttribute('href')?.trim());
  }

  sync() {
    const cards = [...this.rail.querySelectorAll('[data-rail-card]')];
    let available = 0;
    cards.forEach((card) => {
      const meaningful = [...card.querySelectorAll('[data-rail-content]')]
        .some((node) => this.isMeaningful(node));
      card.hidden = !meaningful;
      const shortcut = this.rail.querySelector(`[data-rail-target="${card.id}"]`);
      if (shortcut) shortcut.hidden = !meaningful;
      if (meaningful) available += 1;
    });

    const empty = available === 0;
    this.root.dataset.rightContent = empty ? 'empty' : 'available';
    this.rail.hidden = empty;
    this.toggle.hidden = empty;
    this.toggle.disabled = empty;
    if (empty && this.root.dataset.drawerOpen === 'right') this.sidebarController?.closeDrawer(false);
  }

  init() {
    if (!this.rail || !this.toggle) return;
    this.sync();
    this.observer = new MutationObserver(() => this.sync());
    this.observer.observe(this.rail, { childList: true, subtree: true, characterData: true });
  }
}

const sidebarController = new SidebarController();
sidebarController.init();
new ChapterTreeController().init();
new SearchController().init();
new CopyController().init();
new EvidenceRailController(document, sidebarController).init();

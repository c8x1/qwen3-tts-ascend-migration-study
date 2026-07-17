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

new SidebarController().init();

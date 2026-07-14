/* ════════════════════════════════════════════════════════════════════════════
   MSMS — app.js
   Core UI behaviours: flash auto-dismiss, sidebar active link,
   notification polling, mobile sidebar toggle.
   ════════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Flash message auto-dismiss (5 s) ───────────────────────────────────── */
  function initFlashDismiss() {
    const alerts = document.querySelectorAll('.flash-container .alert[data-auto-dismiss]');
    alerts.forEach(function (alert) {
      const delay = parseInt(alert.dataset.autoDismiss || '5000', 10);
      setTimeout(function () {
        alert.style.transition = 'opacity .4s ease, max-height .4s ease';
        alert.style.opacity = '0';
        alert.style.overflow = 'hidden';
        alert.style.maxHeight = '0';
        alert.style.padding = '0';
        alert.style.margin = '0';
        setTimeout(function () { alert.remove(); }, 420);
      }, delay);
    });
  }

  /* ── Sidebar active link ─────────────────────────────────────────────────── */
  function initSidebarActive() {
    const currentPath = window.location.pathname.replace(/\/$/, '');
    const links = document.querySelectorAll('.sidebar-link');

    links.forEach(function (link) {
      const href = (link.getAttribute('href') || '').replace(/\/$/, '');
      if (!href || href === '#') return;

      // Exact match, or sub-path (but not root '/')
      const isActive = (href === currentPath) ||
        (href !== '' && href !== '/' && currentPath.startsWith(href));

      if (isActive) {
        link.classList.add('active');
        // If inside a collapsible, expand it
        const submenu = link.closest('.sidebar-submenu');
        if (submenu) {
          submenu.style.maxHeight = submenu.scrollHeight + 'px';
          const trigger = submenu.previousElementSibling;
          if (trigger) trigger.classList.add('active');
        }
      }
    });
  }

  /* ── Sidebar collapsibles ────────────────────────────────────────────────── */
  function initSidebarCollapsibles() {
    const triggers = document.querySelectorAll('[data-sidebar-toggle]');
    triggers.forEach(function (trigger) {
      const targetId = trigger.dataset.sidebarToggle;
      const target   = document.getElementById(targetId);
      if (!target) return;

      // Set initial state
      if (!target.style.maxHeight) {
        target.style.maxHeight = '0px';
        target.style.overflow  = 'hidden';
        target.style.transition = 'max-height .2s ease';
      }

      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        const isOpen = target.style.maxHeight !== '0px';
        target.style.maxHeight = isOpen ? '0px' : (target.scrollHeight + 'px');
        trigger.classList.toggle('active', !isOpen);
      });
    });
  }

  /* ── Mobile sidebar toggle ───────────────────────────────────────────────── */
  function initMobileSidebar() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar   = document.querySelector('.sidebar');
    const overlay   = document.getElementById('sidebarOverlay');
    if (!toggleBtn || !sidebar) return;

    function openSidebar() {
      sidebar.classList.add('open');
      if (overlay) overlay.style.display = 'block';
    }

    function closeSidebar() {
      sidebar.classList.remove('open');
      if (overlay) overlay.style.display = 'none';
    }

    toggleBtn.addEventListener('click', function () {
      sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
    });

    if (overlay) {
      overlay.addEventListener('click', closeSidebar);
    }
  }

  /* ── Notification count poll (every 60 s) ───────────────────────────────── */
  function initNotificationPoll() {
    const badge = document.getElementById('notifBadge');
    if (!badge) return;

    function fetchCount() {
      fetch('/notifications/unread-count', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      })
        .then(function (res) {
          if (!res.ok) return;
          return res.json();
        })
        .then(function (data) {
          if (!data) return;
          const count = parseInt(data.count || '0', 10);
          badge.textContent = count > 99 ? '99+' : String(count);
          badge.style.display = count > 0 ? 'flex' : 'none';
        })
        .catch(function () { /* silently ignore — endpoint may not exist yet */ });
    }

    // Initial fetch then every 60 s
    fetchCount();
    setInterval(fetchCount, 60000);
  }

  /* ── Confirm-delete buttons ──────────────────────────────────────────────── */
  function initConfirmDelete() {
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-confirm]');
      if (!btn) return;
      const msg = btn.dataset.confirm || 'Are you sure? This action cannot be undone.';
      if (!window.confirm(msg)) {
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    });
  }

  /* ── Tooltip init (Bootstrap) ────────────────────────────────────────────── */
  function initTooltips() {
    if (typeof bootstrap === 'undefined') return;
    const els = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    els.forEach(function (el) {
      new bootstrap.Tooltip(el, { trigger: 'hover focus' });
    });
  }

  /* ── Table row click-through ─────────────────────────────────────────────── */
  function initRowLinks() {
    document.querySelectorAll('tr[data-href]').forEach(function (row) {
      row.style.cursor = 'pointer';
      row.addEventListener('click', function (e) {
        if (e.target.closest('a, button, input, select')) return;
        window.location.href = row.dataset.href;
      });
    });
  }

  /* ── Init ────────────────────────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    initFlashDismiss();
    initSidebarActive();
    initSidebarCollapsibles();
    initMobileSidebar();
    initNotificationPoll();
    initConfirmDelete();
    initTooltips();
    initRowLinks();
  });

})();

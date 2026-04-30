/**
 * Utility Functions
 * Formatting and helper functions
 */

export function formatDate(value) {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleDateString('ru-RU');
}

export function formatMoney(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(amount);
}

/**
 * Get status class for a filial based on its revision date
 */
export function getStatusClass(filial) {
  if (!filial.next_revision_date) return 'none';

  const nextDate = new Date(filial.next_revision_date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (nextDate < today) {
    return 'overdue';
  }

  return filial.next_revision_status === 'postponed' ? 'postponed' : 'planned';
}

/**
 * Get status color based on status class
 */
export function getStatusColor(statusClass) {
  switch (statusClass) {
    case 'planned':
      return { bg: '#d5f5e3', border: '#2ecc71', text: '#27ae60', indicator: '#2ecc71' };
    case 'postponed':
      return { bg: '#fef9e7', border: '#f1c40f', text: '#d4a017', indicator: '#f1c40f' };
    case 'overdue':
      return { bg: '#fadbd8', border: '#e74c3c', text: '#c0392b', indicator: '#e74c3c' };
    default:
      return { bg: '#ecf2f5', border: '#cfdae0', text: '#354753', indicator: '#999' };
  }
}

/**
 * Validate form data
 */
export function validateCreateForm(name, firstDate, shortage) {
  if (!name.trim() || !firstDate) {
    return { valid: false, error: 'Укажите название и первую дату ревизии.' };
  }

  const amount = Number(shortage || 0);
  if (Number.isNaN(amount) || amount < 0) {
    return { valid: false, error: 'Недостача должна быть числом от 0.' };
  }

  return { valid: true };
}

/**
 * Sort filials by next revision date (default)
 */
export function sortFilials(filials) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return [...filials].sort((a, b) => {
    const aHasNext = !!a.next_revision_date;
    const bHasNext = !!b.next_revision_date;

    if (!aHasNext && !bHasNext) return 0;
    if (!aHasNext) return 1;
    if (!bHasNext) return -1;

    const aDate = new Date(a.next_revision_date);
    const bDate = new Date(b.next_revision_date);
    const aOverdue = aDate < today;
    const bOverdue = bDate < today;

    if (aOverdue && !bOverdue) return -1;
    if (!aOverdue && bOverdue) return 1;

    return aDate.getTime() - bDate.getTime();
  });
}

/**
 * Generic sort function for table columns
 * @param {Array} data - array of objects
 * @param {string} key - property key to sort by
 * @param {string} direction - 'asc' or 'desc'
 * @returns {Array} sorted array
 */
export function sortBy(data, key, direction = 'asc') {
  if (!Array.isArray(data)) return data;

  return [...data].sort((a, b) => {
    const aRaw = a[key];
    const bRaw = b[key];

    // Handle null/undefined
    const aVal = aRaw == null ? '' : aRaw;
    const bVal = bRaw == null ? '' : bRaw;

    let comparison = 0;

    // Date strings (ISO)
    if (key.includes('date') || key.includes('Date')) {
      const aDate = new Date(aVal);
      const bDate = new Date(bVal);
      comparison = aDate.getTime() - bDate.getTime();
    }
    // Numbers
    else if (typeof aVal === 'number' && typeof bVal === 'number') {
      comparison = aVal - bVal;
    }
    // Strings
    else {
      comparison = String(aVal).localeCompare(String(bVal), 'ru-RU');
    }

    return direction === 'asc' ? comparison : -comparison;
  });
}

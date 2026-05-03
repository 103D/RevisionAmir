import { useState, useEffect, useRef } from 'react';
import { DeleteIcon, EditIcon } from './Icons';
import { formatDate, formatMoney, getStatusClass, getStatusColor } from './utils';
import RevisionDatesSlider from './RevisionDatesSlider';

// Debounce helper
function useDebouncedCallback(callback, delay) {
  const timeoutRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const debouncedCallback = (...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  };

  return debouncedCallback;
}

/**
 * Next Revision Date Editor Component
 * Inline editor for next revision date
 */
function NextRevisionEditor({
  filial,
  editState,
  isFeatured,
  isUpdating,
  onStart,
  onSave,
  onCancel,
  onStateChange,
}) {
  const statusClass = getStatusClass(filial);
  const statusColor = getStatusColor(statusClass);
  const isEditing = editState?.editing === 'next';

  // Debounced state change for date input (300ms)
  const debouncedStateChange = useDebouncedCallback((newState) => {
    onStateChange(newState);
  }, 300);

  if (isEditing) {
    return (
      <div className="inlineEdit">
        <input
          type="date"
          value={editState.nextDate}
          onChange={(e) =>
            debouncedStateChange({
              ...editState,
              nextDate: e.target.value,
            })
          }
        />
        <small className="helpText">
          Дата: {new Date(editState.nextDate).toLocaleDateString('ru-RU')}
          <br />
          {editState.originalDate === editState.nextDate
            ? 'Статус: Запланирована (зеленый)'
            : 'Статус: Отложена (желтый)'}
        </small>
        <div className="inlineActions">
          <button
            type="button"
            className={isFeatured ? 'primaryButton primaryButtonFeatured' : 'primaryButton'}
            onClick={onSave}
            disabled={isUpdating}>
            <EditIcon /> Сохранить
          </button>
          <button type="button" className="secondaryButton" onClick={onCancel}>
            Отмена
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      className={isFeatured ? 'nextDateButton nextDateButtonFeatured' : 'nextDateButton'}
      onClick={onStart}
      style={{
        backgroundColor: statusColor.bg,
        borderColor: statusColor.border,
        color: statusColor.text,
        fontSize: isFeatured ? '6rem' : 'inherit',
        padding: isFeatured ? '14px 20px' : '10px 12px',
        minWidth: isFeatured ? '140px' : 'inherit',
      }}>
      {formatDate(filial.next_revision_date)}
    </button>
  );
}

/**
 * Shortage Editor Component
 * Inline editor for shortage value
 */
function ShortageEditor({
  filial,
  editState,
  isFeatured,
  isUpdating,
  onStart,
  onSave,
  onCancel,
  onStateChange,
}) {
  const isEditing = editState?.editing === 'shortage';

  // Debounced state change for shortage input (300ms)
  const debouncedStateChange = useDebouncedCallback((newState) => {
    onStateChange(newState);
  }, 300);

  if (isEditing) {
    return (
      <div className="inlineEdit">
        <input
          type="number"
          min="0"
          step="0.01"
          value={editState.shortage}
          onChange={(e) =>
            debouncedStateChange({
              ...editState,
              shortage: e.target.value,
            })
          }
        />
        <div className="inlineActions">
          <button
            type="button"
            className={isFeatured ? 'primaryButton primaryButtonFeatured' : 'primaryButton'}
            onClick={onSave}
            disabled={isUpdating}>
            ОК
          </button>
          <button type="button" className="secondaryButton" onClick={onCancel}>
            Отмена
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="shortageRow">
      <strong className={isFeatured ? 'shortageValue shortageValueFeatured' : 'shortageValue'}>
        {formatMoney(filial.shortage)} тг
      </strong>
      <button
        type="button"
        className={isFeatured ? 'secondaryButton secondaryButtonFeatured' : 'secondaryButton'}
        onClick={onStart}
        title="Изменить недостачу">
        <EditIcon />
      </button>
    </div>
  );
}

/**
 * Filial Card Component
 * Individual branch card with edit functionality
 */
function FilialCard({
  filial,
  isFeatured,
  editState,
  onStartNextEdit,
  onStartShortageEdit,
  onCancelEdit,
  onSaveNextEdit,
  onSaveShortageEdit,
  onDelete,
  onEditStateChange,
  isUpdatingNext,
  isUpdatingShortage,
  isDeleting,
}) {
  // Determine status color for the featured indicator
  const statusClass = getStatusClass(filial);
  const statusColor = getStatusColor(statusClass);
  return (
    <article
      key={filial.id}
      className={isFeatured ? 'card featuredCard' : 'card'}
      style={{ position: 'relative' }}>
      {/* Delete Button */}

      {/* Card Header */}
      <header className="cardHead">
        <h3 className={isFeatured ? 'cardTitle featuredTitle' : 'cardTitle'}>{filial.name}</h3>
        <button
          type="button"
          className="deleteButton"
          onClick={onDelete}
          disabled={isDeleting}
          title="Удалить филиал"
          aria-label={`Удалить филиал ${filial.name}`}>
          <DeleteIcon />
        </button>
      </header>

      {/* Revision Dates Info */}
      <div className="dateBlock">
        <div className={isFeatured ? 'nextDateBlock nextDateButtonFeatured' : 'nextDateBlock'}>
          <span className={isFeatured ? 'metaLabel metaLabelFeatured' : 'metaLabel'}>
            Следующая ревизия
          </span>
          {/* <div className="dateRow">
            <span className="dateLabel">
              {filial.next_revision_date ? formatDate(filial.next_revision_date) : '-'}
            </span>
          </div> */}
          <NextRevisionEditor
            filial={filial}
            editState={editState}
            isFeatured={isFeatured}
            isUpdating={isUpdatingNext}
            onStart={onStartNextEdit}
            onSave={onSaveNextEdit}
            onCancel={onCancelEdit}
            onStateChange={onEditStateChange}
          />
        </div>

        {/* Previous Revision Block */}
        <div className={isFeatured ? 'prevDateBlock prevDateBlockFeatured' : 'prevDateBlock'}>
          <span className={isFeatured ? 'metaLabel metaLabelFeatured' : 'metaLabel'}>
            Прошлая ревизия
          </span>
          {/* <div className="dateRow">
            <span className="dateLabel">
              {filial.previous_revision_date ? (
                formatDate(filial.previous_revision_date)
              ) : (
                <span className="emptyCell">Нет проведённых ревизий</span>
              )}
            </span>
          </div> */}
        </div>

        {/* Shortage Block */}
        <div className={isFeatured ? 'shortageBlock shortageBlockFeatured' : 'shortageBlock'}>
          <span className={isFeatured ? 'metaLabel metaLabelFeatured' : 'metaLabel'}>
            Итоговая недостача
          </span>
          <ShortageEditor
            filial={filial}
            editState={editState}
            isFeatured={isFeatured}
            isUpdating={isUpdatingShortage}
            onStart={onStartShortageEdit}
            onSave={onSaveShortageEdit}
            onCancel={onCancelEdit}
            onStateChange={onEditStateChange}
          />
          <RevisionDatesSlider filial={filial} isFeatured={isFeatured} />
        </div>
      </div>
    </article>
  );
}

export default FilialCard;

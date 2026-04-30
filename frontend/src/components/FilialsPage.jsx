import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { filialsApi, exportApi } from '../services/api';
import FilialCard from './FilialCard';
import CreateFilialForm from './CreateFilialForm';
import RevisionDatesSlider from './RevisionDatesSlider';
import { getStatusClass, sortFilials, sortBy } from './utils';
import { DownloadIcon, GridIcon, TableIcon, TrashIcon, ChevronUpIcon, ChevronDownIcon } from './Icons';
import './FilialsPage.css';

/**
 * Filials Management Page Component
 * Main page for managing branch revisions
 */
function FilialsPage() {
  const queryClient = useQueryClient();
  const [editStates, setEditStates] = useState({});
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'
  const [tableSort, setTableSort] = useState({ key: 'next_revision_date', dir: 'asc' });

  // ============================================================
  // Queries & Mutations
  // ============================================================
  const filialsQuery = useQuery({
    queryKey: ['filials'],
    queryFn: () => filialsApi.getAll(),
  });

  const createMutation = useMutation({
    mutationFn: (payload) => filialsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filials'] });
      toast.success('Филиал добавлен');
    },
    onError: (error) => toast.error(error.message),
  });

  const updateNextMutation = useMutation({
    mutationFn: ({ id, next_revision_date, status }) =>
      filialsApi.updateNextRevision(id, next_revision_date, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filials'] });
      toast.success('Следующая ревизия обновлена');
    },
    onError: (error) => toast.error(error.message),
  });

  const updateShortageMutation = useMutation({
    mutationFn: ({ id, shortage }) => filialsApi.update(id, { shortage }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filials'] });
      toast.success('Недостача обновлена');
    },
    onError: (error) => toast.error(error.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => filialsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filials'] });
      toast.success('Филиал удален');
    },
    onError: (error) => toast.error(error.message),
  });

  const exportFilialsMutation = useMutation({
    mutationFn: () => exportApi.downloadFilials(),
    onError: (error) => toast.error(error.message),
  });

  const exportHolidaysMutation = useMutation({
    mutationFn: () => exportApi.downloadHolidays(),
    onError: (error) => toast.error(error.message),
  });

  // ============================================================
  // Sorting & Editing Helpers
  // ============================================================
  const sortedFilials = useMemo(() => {
    return filialsQuery.data ? sortFilials(filialsQuery.data) : [];
  }, [filialsQuery.data]);

  const sortedTableFilials = useMemo(() => {
    if (!filialsQuery.data) return [];
    return sortBy(filialsQuery.data, tableSort.key, tableSort.dir);
  }, [filialsQuery.data, tableSort]);

  const handleSort = (key) => {
    setTableSort((prev) => ({
      key,
      dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc',
    }));
  };

  const startNextEdit = (filial) => {
    if (!filial.next_revision_date) return;
    setEditStates((prev) => ({
      ...prev,
      [filial.id]: {
        nextDate: filial.next_revision_date.slice(0, 10),
        originalDate: filial.next_revision_date.slice(0, 10),
        shortage: String(filial.shortage ?? 0),
        editing: 'next',
      },
    }));
  };

  const startShortageEdit = (filial) => {
    setEditStates((prev) => ({
      ...prev,
      [filial.id]: {
        nextDate: filial.next_revision_date?.slice(0, 10) || '',
        originalDate: filial.next_revision_date?.slice(0, 10) || '',
        shortage: String(filial.shortage ?? 0),
        editing: 'shortage',
      },
    }));
  };

  const cancelEdit = (id) => {
    setEditStates((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const saveNextEdit = (id) => {
    const state = editStates[id];
    if (!state?.nextDate) return;
    const status = state.originalDate === state.nextDate ? 'planned' : 'postponed';
    updateNextMutation.mutate(
      { id, next_revision_date: state.nextDate, status },
      { onSuccess: () => cancelEdit(id) },
    );
  };

  const saveShortageEdit = (id) => {
    const state = editStates[id];
    if (!state) return;
    const amount = Number(state.shortage);
    if (Number.isNaN(amount) || amount < 0) return;
    updateShortageMutation.mutate(
      { id, shortage: amount },
      { onSuccess: () => cancelEdit(id) },
    );
  };

  const deleteFilial = (filial) => {
    if (window.confirm(`Удалить филиал «${filial.name}»?`)) {
      deleteMutation.mutate(filial.id);
    }
  };

  // ============================================================
  // Render
  // ============================================================
  return (
    <section className="page">
      {/* Create Filial Form */}
      <CreateFilialForm
        onSubmit={(payload) => createMutation.mutate(payload)}
        isPending={createMutation.isPending}
      />

      {/* Toolbar: View Toggle + Export */}
      <div className="toolbar">
        <div className="viewToggle">
          <button
            type="button"
            className={`viewButton ${viewMode === 'cards' ? 'active' : ''}`}
            onClick={() => setViewMode('cards')}
            title="Вид карточками"
          >
            <GridIcon /> Карточки
          </button>
          <button
            type="button"
            className={`viewButton ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => setViewMode('table')}
            title="Таблица"
          >
            <TableIcon /> Таблица
          </button>
        </div>

        {/* Export Controls */}
        <div className="exportControls">
          <h2 className="exportTitle">Экспорт данных</h2>
          <div className="exportButtons">
            <button
              type="button"
              className="exportButton"
              onClick={() => exportFilialsMutation.mutate()}
              disabled={exportFilialsMutation.isPending}
            >
              <DownloadIcon /> Экспорт филиалов (Excel)
            </button>
            <button
              type="button"
              className="exportButton"
              onClick={() => exportHolidaysMutation.mutate()}
              disabled={exportHolidaysMutation.isPending}
            >
              <DownloadIcon /> Экспорт праздников (Excel)
            </button>
          </div>
        </div>
      </div>

      {/* Filials List */}
      <section className="panel">
        {filialsQuery.isLoading && <p className="systemState">Загрузка списка...</p>}
        {filialsQuery.isError && <p className="systemStateError">Не удалось загрузить данные.</p>}
        {!filialsQuery.isLoading && sortedFilials.length === 0 && (
          <p className="systemState">Филиалов пока нет.</p>
        )}

        {viewMode === 'cards' ? (
          <div className="cards">
            {sortedFilials.map((filial, index) => (
              <FilialCard
                key={filial.id}
                filial={filial}
                isFeatured={index === 0}
                editState={editStates[filial.id]}
                onStartNextEdit={() => startNextEdit(filial)}
                onStartShortageEdit={() => startShortageEdit(filial)}
                onCancelEdit={() => cancelEdit(filial.id)}
                onSaveNextEdit={() => saveNextEdit(filial.id)}
                onSaveShortageEdit={() => saveShortageEdit(filial.id)}
                onDelete={() => deleteFilial(filial)}
                onEditStateChange={(newState) =>
                  setEditStates((prev) => ({
                    ...prev,
                    [filial.id]: newState,
                  }))
                }
                isUpdatingNext={updateNextMutation.isPending}
                isUpdatingShortage={updateShortageMutation.isPending}
                isDeleting={deleteMutation.isPending}
              />
            ))}
          </div>
        ) : (
          <div className="tableWrapper">
            <table className="filialsTable">
              <thead>
                <tr>
                  <th onClick={() => handleSort('name')} className="sortable">
                    Название
                    {tableSort.key === 'name' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th onClick={() => handleSort('first_revision_date')} className="sortable">
                    Первая ревизия
                    {tableSort.key === 'first_revision_date' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th onClick={() => handleSort('previous_revision_date')} className="sortable">
                    Предыдущая
                    {tableSort.key === 'previous_revision_date' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th onClick={() => handleSort('next_revision_date')} className="sortable">
                    Следующая
                    {tableSort.key === 'next_revision_date' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th onClick={() => handleSort('next_revision_status')} className="sortable">
                    Статус
                    {tableSort.key === 'next_revision_status' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th onClick={() => handleSort('shortage')} className="sortable numeric">
                    Недостача
                    {tableSort.key === 'shortage' && (
                      tableSort.dir === 'asc' ? <ChevronUpIcon /> : <ChevronDownIcon />
                    )}
                  </th>
                  <th>Даты ревизий</th>
                  <th className="actions-col">Действия</th>
                </tr>
              </thead>
              <tbody>
                {sortedTableFilials.map((filial) => (
                  <tr key={filial.id}>
                    <td className="col-name">{filial.name}</td>
                    <td>{filial.first_revision_date}</td>
                    <td>{filial.previous_revision_date || '-'}</td>
                    <td>{filial.next_revision_date || '-'}</td>
                    <td>
                      <span className={`statusBadge ${filial.next_revision_status}`}>
                        {filial.next_revision_status === 'planned' ? 'Запланирована' : 'Отложена'}
                      </span>
                    </td>
                    <td className="col-amount">{filial.shortage?.toLocaleString() ?? 0} тг</td>
                    <td className="col-dates">
                      {filial.revision_dates && filial.revision_dates.length > 0 ? (
                        <RevisionDatesSlider filial={filial} isFeatured={false} />
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="actions-col">
                      <div className="tableActions">
                        <button
                          type="button"
                          className="actionButton delete"
                          onClick={() => deleteFilial(filial)}
                          disabled={deleteMutation.isPending}
                          title="Удалить"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}

export default FilialsPage;

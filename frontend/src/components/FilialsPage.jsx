import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { filialsApi } from '../services/api';
import FilialCard from './FilialCard';
import CreateFilialForm from './CreateFilialForm';
import { getStatusClass, sortFilials } from './utils';
import './FilialsPage.css';

/**
 * Filials Management Page Component
 * Main page for managing branch revisions
 */
function FilialsPage() {
  const queryClient = useQueryClient();
  const [editStates, setEditStates] = useState({});

  // ============================================================
  // Queries & Mutations
  // ============================================================
  const filialsQuery = useQuery({
    queryKey: ['filials'],
    queryFn: () => filialsApi.getAll(),
  });

  const exportFilialsMutation = useMutation({
    mutationFn: () => exportApi.downloadFilials(),
    onError: (error) => toast.error(error.message),
  });

  const exportHolidaysMutation = useMutation({
    mutationFn: () => exportApi.downloadHolidays(),
    onError: (error) => toast.error(error.message),
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

  // ============================================================
  // Sorting
  // ============================================================
  const sortedFilials = useMemo(() => {
    return filialsQuery.data ? sortFilials(filialsQuery.data) : [];
  }, [filialsQuery.data]);

  // ============================================================
  // Edit Handlers
  // ============================================================
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
      {
        onSuccess: () => cancelEdit(id),
      },
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

       {/* Filials List */}
       <section className="panel">
        {filialsQuery.isLoading && <p className="systemState">Загрузка списка...</p>}

        {filialsQuery.isError && <p className="systemStateError">Не удалось загрузить данные.</p>}

        {!filialsQuery.isLoading && sortedFilials.length === 0 && (
          <p className="systemState">Филиалов пока нет.</p>
        )}

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
      </section>
    </section>
  );
}

export default FilialsPage;

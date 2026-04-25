import { useState } from 'react';

import { PlusIcon } from './Icons';

/**
 * Create Filial Form Component
 * Form for adding new branches
 */
function CreateFilialForm({ onSubmit, isPending }) {
  const [form, setForm] = useState({
    name: '',
    first_revision_date: '',
    shortage: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    const { name, first_revision_date, shortage } = form;
    if (!name.trim() || !first_revision_date) {
      return;
    }

    const shortageAmount = Number(shortage || 0);
    if (Number.isNaN(shortageAmount) || shortageAmount < 0) {
      return;
    }

    onSubmit({
      name: name.trim(),
      first_revision_date,
      shortage: shortageAmount,
    });

    setForm({
      name: '',
      first_revision_date: '',
      shortage: '',
    });
  };

  return (
    <section className="panel">
      <h2 className="panelTitle">Добавить филиал</h2>
      <form onSubmit={handleSubmit} className="formGrid">
        <label className="field">
          <span>Название</span>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="Например, Алматы Юг"
            required
            maxLength={100}
          />
        </label>

        <label className="field">
          <span>Первая ревизия</span>
          <input
            type="date"
            value={form.first_revision_date}
            onChange={(e) => setForm((p) => ({ ...p, first_revision_date: e.target.value }))}
            required
          />
        </label>

        {/* <label className="field">
          <span>Недостача (итог)</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.shortage}
            onChange={(e) => setForm((p) => ({ ...p, shortage: e.target.value }))}
            placeholder="0"
          />
        </label> */}

        <button
          type="submit"
          className="primaryButton"
          disabled={isPending}>
          <PlusIcon />
          {isPending ? 'Сохранение...' : 'Добавить'}
        </button>
      </form>
    </section>
  );
}

export default CreateFilialForm;

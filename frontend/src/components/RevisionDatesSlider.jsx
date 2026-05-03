import { useState, useMemo } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from './Icons';
import { formatDate } from './utils';

/**
 * Revision Dates Slider Component
 * Shows one revision date at a time with prev/next navigation
 */
function RevisionDatesSlider({ filial, isFeatured }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Получаем даты ревизий
  const revisionDates = useMemo(() => {
    const dates = filial?.revision_dates || [];
    return dates.map((d) => new Date(d)).sort((a, b) => a - b);
  }, [filial?.revision_dates]);

  const totalDates = revisionDates.length;

  // Текущая дата
  const currentDate = revisionDates[currentIndex];

  // Получаем недостачу и статус для текущей даты
  const shortage = filial?.revision_shortages?.[currentDate.toISOString().split('T')[0]] || 0;
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];
  const currentStr = currentDate.toISOString().split('T')[0];

  const status = filial?.revision_statuses?.[currentStr] || 'planned';
  const isPast = currentDate < today;
  const isToday = currentDate.toDateString() === today.toDateString();
  const isFuture = currentDate > today;

  const statusClass = isPast ? 'past' : isToday ? 'today' : 'future';
  const statusLabel = isPast ? 'Прошлая' : isToday ? 'Сегодня' : 'Будущая';

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev < totalDates - 1 ? prev + 1 : prev));
  };

  if (totalDates === 0) {
    return <div className="revisionSlider">Нет дат ревизий</div>;
  }

  return (
    <div className={`revisionSlider ${isFeatured ? 'revisionSliderFeatured' : ''}`}>
      <div className="sliderHeader">
        <span className="sliderLabel">Даты ревизий</span>
        <span className="sliderCounter">
          {currentIndex + 1} / {totalDates}
        </span>
      </div>

      <div className={`sliderDisplay ${statusClass}`}>
        <button
          type="button"
          className="sliderArrow sliderArrowLeft"
          onClick={goToPrevious}
          disabled={currentIndex === 0}
          aria-label="Предыдущая дата">
          <ChevronLeftIcon />
        </button>

        <div className="sliderDateContainer">
          <span className="sliderDateLabel">{statusLabel}</span>
          <span className={`sliderDate ${isFeatured ? 'sliderDateFeatured' : ''}`}>
            {formatDate(currentDate)}
          </span>
          {isToday && <span className="todayBadge">Сегодня</span>}
          <div className="sliderInfo">
            {/* <span className="sliderInfoStatus">
              Статус: {status === 'planned' ? 'Запланирована' : 'Отложена'}
            </span> */}
            <br /> 
            <span className="sliderInfoShortage">
              Недостача: {shortage?.toLocaleString() || 0} тг
            </span>
          </div>
        </div>

        <button
          type="button"
          className="sliderArrow sliderArrowRight"
          onClick={goToNext}
          disabled={currentIndex === totalDates - 1}
          aria-label="Следующая дата">
          <ChevronRightIcon />
        </button>
      </div>

      {/* Progress dots */}
      <div className="sliderDots">
        {revisionDates.map((_, idx) => (
          <button
            key={idx}
            type="button"
            className={`sliderDot ${idx === currentIndex ? 'active' : ''}`}
            onClick={() => setCurrentIndex(idx)}
            aria-label={`Перейти к дате ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

export default RevisionDatesSlider;

import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from './Icons';
import { formatDate } from './utils';

/**
 * Revision Dates Slider Component
 * Shows one revision date at a time with prev/next navigation
 */
function RevisionDatesSlider({ filial, isFeatured }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const revisionDates = filial.revision_dates || [];
  const totalDates = revisionDates.length;

  // If no dates, show placeholder
  if (totalDates === 0) {
    return (
      <div className={`revisionSlider revisionSliderEmpty ${isFeatured ? 'revisionSliderFeatured' : ''}`}>
        <div className="sliderHeader">
          <span className="sliderLabel">Даты ревизий</span>
        </div>
        <div className="sliderEmptyState">
          <span>Нет запланированных ревизий</span>
        </div>
      </div>
    );
  }

  const currentDate = revisionDates[currentIndex];

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev < totalDates - 1 ? prev + 1 : prev));
  };

  // Determine status for current date
  const today = new Date();
  const currentDateObj = new Date(currentDate);
  const isPast = currentDateObj < today;
  const isToday = currentDateObj.toDateString() === today.toDateString();
  const isFuture = currentDateObj > today;

  const statusClass = isPast ? 'past' : isToday ? 'today' : 'future';
  const statusLabel = isPast ? 'Прошлая' : isToday ? 'Сегодня' : 'Будущая';

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
          aria-label="Предыдущая дата"
        >
          <ChevronLeftIcon />
        </button>

        <div className="sliderDateContainer">
          <span className="sliderDateLabel">{statusLabel}</span>
          <span className={`sliderDate ${isFeatured ? 'sliderDateFeatured' : ''}`}>
            {formatDate(currentDate)}
          </span>
          {isToday && <span className="todayBadge">Сегодня</span>}
        </div>

        <button
          type="button"
          className="sliderArrow sliderArrowRight"
          onClick={goToNext}
          disabled={currentIndex === totalDates - 1}
          aria-label="Следующая дата"
        >
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

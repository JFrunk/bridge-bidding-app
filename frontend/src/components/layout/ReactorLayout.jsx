/**
 * ReactorLayout - Centripetal 3x3 Grid Layout
 * Physics v2.0 compliant - all dimensions in em units
 *
 * The "Reactor Core" layout centers the TrickArena with hands orbiting around it.
 * Grid structure:
 *   [empty]  [North]  [empty]
 *   [West]   [Arena]  [East]
 *   [empty]  [South]  [empty]
 *
 * Design principles:
 * - Center (Arena) is the visual anchor - hands "hug" toward it
 * - Dynamic gap allows hands to stay close without overlapping
 * - All hands face inward toward the center
 * - No cards bleed into the center arena space
 */
import React from 'react';

const ReactorLayout = ({
  north,      // North hand component (partner when dummy, or declarer)
  south,      // South hand component (player's hand)
  east,       // East hand component (opponent/dummy)
  west,       // West hand component (opponent/dummy)
  center,     // TrickArena component
  scaleClass = 'text-base',  // Base scale for the entire layout
  className = ''
}) => {
  return (
    <div className={`${scaleClass} ${className}`}>
      {/* Centripetal 3x3 Grid - hands orbit around center arena */}
      <div className="
        grid
        grid-cols-[auto_minmax(20em,1fr)_auto]
        grid-rows-[auto_minmax(18em,1fr)_auto]
        gap-[0.5em]
        items-center
        justify-items-center
        w-full
        max-w-[60em]
        mx-auto
        p-[1em]
        bg-[var(--table-green,#1a6b3c)]
        rounded-lg
      ">
        {/* Row 1: Empty - North - Empty */}
        <div className="col-start-1 row-start-1" />
        <div className="col-start-2 row-start-1 flex justify-center">
          {north}
        </div>
        <div className="col-start-3 row-start-1" />

        {/* Row 2: West - Arena (Center) - East */}
        <div className="col-start-1 row-start-2 flex items-center justify-end pr-[0.5em]">
          {west}
        </div>
        <div className="col-start-2 row-start-2 flex items-center justify-center">
          {center}
        </div>
        <div className="col-start-3 row-start-2 flex items-center justify-start pl-[0.5em]">
          {east}
        </div>

        {/* Row 3: Empty - South - Empty */}
        <div className="col-start-1 row-start-3" />
        <div className="col-start-2 row-start-3 flex justify-center">
          {south}
        </div>
        <div className="col-start-3 row-start-3" />
      </div>
    </div>
  );
};

export default ReactorLayout;

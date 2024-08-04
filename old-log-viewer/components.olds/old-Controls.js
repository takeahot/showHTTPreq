import React from 'react';

const Controls = ({ columns, setRefreshInterval }) => {
  return (
    <div className="top-bar">
      <div className="refresh-group">
        <label>Auto-refresh (seconds):
          <input type="number" min="5" step="5" onChange={(e) => setRefreshInterval(e.target.value)} />
        </label>
      </div>
    </div>
  );
};

export default Controls;

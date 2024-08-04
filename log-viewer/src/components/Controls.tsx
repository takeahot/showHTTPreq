import React, { FC } from 'react';

interface ControlsProps {
  columns: string[]; 
  setRefreshInterval: (value: number) => void;
}

const Controls: FC<ControlsProps> = ({ columns, setRefreshInterval }) => {
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRefreshInterval(Number(e.target.value));
  };

  return (
    <div className="top-bar">
      <div className="refresh-group">
        <label>Auto-refresh (seconds):
          <input type="number" min="5" step="5" onChange={handleInputChange} />
        </label>
      </div>
    </div>
  );
};

export default Controls;
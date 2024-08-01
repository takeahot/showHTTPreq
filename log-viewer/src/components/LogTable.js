import React from 'react';
import './LogTable.css';

const LogTable = ({ logs, columns, colWidths, onCellClick, onColumnResizeStart, tableRef }) => {
    return (
        <div ref={tableRef} className="log-table" style={{ gridTemplateColumns: colWidths.map(width => `${width}px`).join(' ') }}>
            {columns.map((col, colIndex) => (
                <div key={`header-${colIndex}`} className="log-table-header">
                    {col}
                    <div
                        className="resize-handle"
                        onMouseDown={(e) => onColumnResizeStart(colIndex, e)}
                    />
                </div>
            ))}
            {logs.map((log, rowIndex) => (
                columns.map((col, colIndex) => (
                    <div
                        key={`${rowIndex}-${colIndex}`}
                        className="log-table-cell"
                        onClick={() => onCellClick(log[col])}
                    >
                        {typeof log[col] === 'object' ? JSON.stringify(log[col]) : log[col]}
                    </div>
                ))
            ))}
        </div>
    );
};

export default LogTable;

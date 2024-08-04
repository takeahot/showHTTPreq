import React, { FC } from 'react';
import './LogTable.css';

interface LogTableProps {
    logs: Array<{ [key: string]: any }>;
    columns: string[];
    colWidths: number[];
    onCellClick: (content: any, event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
    onColumnResizeStart: (index: number, event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
    tableRef: React.RefObject<HTMLDivElement>;
}

const LogTable: FC<LogTableProps> = ({ logs, columns, colWidths, onCellClick, onColumnResizeStart, tableRef }) => {
    return (
        <div
            ref={tableRef}
            className="log-table"
            style={{ gridTemplateColumns: colWidths.map(width => `${width}px`).join(' ') }}
        >
            {columns.map((col, colIndex) => (
                <div key={`header-${colIndex}`} className="log-table-header">
                    {col}
                    <div
                        className="resize-handle"
                        onMouseDown={(e) => onColumnResizeStart(colIndex, e)}
                    />
                </div>
            ))}
            {logs.map((log, rowIndex) =>
                columns.map((col, colIndex) => (
                    <div
                        key={`${rowIndex}-${colIndex}`}
                        className="log-table-cell"
                        onClick={(e) => onCellClick(log[col], e)}
                    >
                        {typeof log[col] === 'object' ? JSON.stringify(log[col]) : log[col]}
                    </div>
                ))
            )}
        </div>
    );
};

export default LogTable;

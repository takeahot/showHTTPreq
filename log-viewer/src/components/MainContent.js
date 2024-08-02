import React, { useState, useEffect, useRef } from 'react';
import LogTable from './LogTable';
import './MainContent.css';

const MainContent = () => {
    const [logs, setLogs] = useState([]);
    const [columns, setColumns] = useState([]);
    const [colWidths, setColWidths] = useState([]);
    const [isResizing, setIsResizing] = useState(false);
    const [currentColIndex, setCurrentColIndex] = useState(null);
    const [startX, setStartX] = useState(0);
    const [startWidth, setStartWidth] = useState(0);
    const [refreshInterval, setRefreshInterval] = useState(30);
    const tableRef = useRef(null);
    const tableScrollBarRef = useRef(null);
    const tableScrollContainerRef = useRef(null);
    const tableWrapperRef = useRef(null);
    const tableContainerRef = useRef(null);
    const bottomBarRef = useRef(null);
    const isSticky = useRef(false); // Флаг для отслеживания приклеенного состояния

    useEffect(() => {
        // Загрузка последних логов при инициализации
        fetch('/logs_last_part')
            .then(response => response.json())
            .then(data => {
                const colKeys = Object.keys(data[0] || {});
                setColumns(colKeys);
                setColWidths(colKeys.map(() => 150)); 
                const logsWithoutHeaders = data.slice(1);
                setLogs(logsWithoutHeaders);
            });
    }, []);

    useEffect(() => {
        const intervalId = setInterval(() => {
            if (logs.length > 0) {
                const lastLogId = logs[logs.length - 1].id;
                fetch(`/logs_after/${lastLogId}`)
                    .then(response => response.json())
                    .then(newLogs => {
                        if (newLogs.length > 1) {  // Проверяем, есть ли новые логи
                            setLogs(prevLogs => [...prevLogs, ...newLogs.slice(1)]); // Обновляем таблицу
                        }
                    });
            }
        }, refreshInterval * 1000);

        return () => clearInterval(intervalId); // Очистка интервала при размонтировании компонента
    }, [logs, refreshInterval]);

    useEffect(() => {
        const updateScrollBarWidth = () => {
            if (tableRef.current && tableScrollBarRef.current) {
                const tableWidth = tableRef.current.scrollWidth;
                tableScrollBarRef.current.style.width = `${tableWidth}px`;
            }
        };

        updateScrollBarWidth();

        const tableScrollContainer = tableScrollContainerRef.current;
        const tableWrapper = tableWrapperRef.current;
        const tableContainer = tableContainerRef.current;
        const bottomBar = bottomBarRef.current;

        if (tableScrollContainer && tableWrapper && tableContainer && bottomBar) {
            const syncScroll = (source, target) => {
                target.scrollLeft = source.scrollLeft;
            };

            const handleTableScrollContainerScroll = () => syncScroll(tableScrollContainer, tableWrapper);
            const handleTableWrapperScroll = () => syncScroll(tableWrapper, tableScrollContainer);

            tableScrollContainer.addEventListener('scroll', handleTableScrollContainerScroll);
            tableWrapper.addEventListener('scroll', handleTableWrapperScroll);

            const updateScrollBarPosition = () => {
                const scrollBarBottom = tableWrapper.getBoundingClientRect().bottom;
                const containerBottom = tableContainer.getBoundingClientRect().bottom;

                if (scrollBarBottom >= containerBottom) {
                    if (!isSticky.current) {
                        tableScrollContainer.classList.add('sticky-scroll-bar');
                        tableScrollContainer.style.position = 'fixed';
                        tableScrollContainer.style.bottom = `${window.innerHeight - containerBottom}px`;
                        isSticky.current = true;
                    }
                } else {
                    if (isSticky.current) {
                        tableScrollContainer.classList.remove('sticky-scroll-bar');
                        tableScrollContainer.style.position = 'relative';
                        tableScrollContainer.style.bottom = '0';
                        isSticky.current = false;
                    }
                }
            };

            tableContainer.addEventListener('scroll', updateScrollBarPosition);
            updateScrollBarPosition(); // Вызовем сразу для корректной начальной позиции

            return () => {
                tableScrollContainer.removeEventListener('scroll', handleTableScrollContainerScroll);
                tableWrapper.removeEventListener('scroll', handleTableWrapperScroll);
                tableContainer.removeEventListener('scroll', updateScrollBarPosition);
            };
        }
    }, [columns, logs]);

    const handleMouseDown = (index, event) => {
        setIsResizing(true);
        setCurrentColIndex(index);
        setStartX(event.clientX);
        setStartWidth(colWidths[index]);
    };

    const handleMouseMove = (event) => {
        if (isResizing && currentColIndex !== null) {
            const deltaX = event.clientX - startX;
            const newWidths = [...colWidths];
            newWidths[currentColIndex] = Math.max(50, startWidth + deltaX); 
            setColWidths(newWidths);
        }
    };

    const handleMouseUp = () => {
        setIsResizing(false);
        setCurrentColIndex(null);
    };

    const handleLoadMore = () => {
        if (logs.length > 0) {
            const firstLogId = logs[0].id;
            fetch(`/logs_before/${firstLogId}`)
                .then(response => response.json())
                .then(previousLogs => {
                    if (previousLogs.length > 1) {
                        setLogs(prevLogs => [...previousLogs.slice(1), ...prevLogs]);
                    }
                });
        }
    };

    if (!columns.length || !logs.length) {
        return <div>Loading...</div>;
    }

    return (
        <div className="main-content" onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
            <aside className="sidebar">
                <button>Button 1</button>
                <button>Button 2</button>
                <button>Button 3</button>
            </aside>
            <section className="content">
                <div className="top-bar">
                    <div className="refresh-group">
                        <label>Auto-refresh (seconds):
                            <input
                                type="number"
                                min="5"
                                step="5"
                                value={refreshInterval}
                                onChange={(e) => setRefreshInterval(e.target.value)}
                            />
                        </label>
                    </div>
                </div>
                <div className="table-container" ref={tableContainerRef}>
                    <div className="table-wrapper" ref={tableWrapperRef}>
                        <LogTable
                            logs={logs}
                            columns={columns}
                            colWidths={colWidths}
                            onCellClick={setLogs}
                            onColumnResizeStart={handleMouseDown}
                            tableRef={tableRef} 
                        />
                    </div>
                    <div className="table-scroll-container" ref={tableScrollContainerRef}>
                        <div
                            className="table-scroll-bar"
                            ref={tableScrollBarRef}
                            style={{ width: tableRef.current ? `${tableRef.current.scrollWidth}px` : '100%' }}
                        ></div>
                    </div>
                    <div className="bottom-bar" ref={bottomBarRef}>
                        <button onClick={handleLoadMore}>Load More Logs</button>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default MainContent;

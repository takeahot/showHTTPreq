import React, { useState, useEffect, useRef } from 'react';
import LogTable from './LogTable';
import './MainContent.css';

interface LogEntry {
    id: number;
    [key: string]: any;
}

interface PopupPosition {
    top: number;
    left: number;
}

const MainContent: React.FC = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [columns, setColumns] = useState<string[]>([]);
    const [colWidths, setColWidths] = useState<number[]>([]);
    const [isResizing, setIsResizing] = useState<boolean>(false);
    const [currentColIndex, setCurrentColIndex] = useState<number | null>(null);
    const [startX, setStartX] = useState<number>(0);
    const [startWidth, setStartWidth] = useState<number>(0);
    const [refreshInterval, setRefreshInterval] = useState<number>(90);
    const [lastUpdated, setLastUpdated] = useState<string>(''); 
    const [popupContent, setPopupContent] = useState<string | null>(null);
    const [popupPosition, setPopupPosition] = useState<PopupPosition>({ top: 0, left: 0 });
    const [viewMode, setViewMode] = useState<'logMonitoring' | 'selectedPeriod'>('logMonitoring');
    const [minId, setMinId] = useState<number | null>(null);
    const [maxId, setMaxId] = useState<number | null>(null);

    const tableRef = useRef<HTMLDivElement | null>(null);
    const tableScrollBarRef = useRef<HTMLDivElement | null>(null);
    const tableScrollContainerRef = useRef<HTMLDivElement | null>(null);
    const tableWrapperRef = useRef<HTMLDivElement | null>(null);
    const tableContainerRef = useRef<HTMLDivElement | null>(null);
    const bottomBarRef = useRef<HTMLDivElement | null>(null);
    const popupRef = useRef<HTMLDivElement | null>(null);
    const isSticky = useRef<boolean>(false);

    // Функция для задания ширины колонок в зависимости от названия
    const getColumnWidth = (columnName: string) => {
        switch (columnName) {
            case 'id':
                return 50; // ширина для id
            case 'ip':
                return 50;
            case 'domain':
                return 50;
            case 'eventName':
                return 493;
            case 'timestamp':
                return 107;
            case 'eventTimestamp':
                return 100;
            case 'eventId':
                return 150;
            case 'internalId':
                return 100;
            case 'number':
                return 50;
            case 'ticketId':
                return 150;
            case 'isTriggeredViaApi':
                return 50; // ширина для isTriggeredViaApi
            case 'body_json':
                return 1940;
            default:
                return 150; // ширина по умолчанию для всех остальных колонок
        }
    };

    useEffect(() => {
        if (viewMode === 'logMonitoring') {
            fetch('/x/logs_last_part')
                .then(response => response.json())
                .then(data => {
                    const colKeys = Object.keys(data[0] || {});
                    setColumns(colKeys);
                    
                    // Устанавливаем ширину колонок на основе их названий
                    const newColWidths = colKeys.map(columnName => getColumnWidth(columnName));
                    setColWidths(newColWidths);

                    // Удаляем дубликаты и сортируем по убыванию id
                    const uniqueLogs = removeDuplicates(data.slice(1));
                    uniqueLogs.sort((a, b) => b.id - a.id);
                    
                    setLogs(uniqueLogs);
                    setLastUpdated(new Date().toISOString());
                });
        }
    }, [viewMode]);

    useEffect(() => {
        if (logs.length > 0) {
            // Обновляем ширину колонок при изменении logs
            const newColWidths = columns.map(columnName => getColumnWidth(columnName));
            setColWidths(newColWidths);
        }
    }, [logs]);

    useEffect(() => {
        if (viewMode === 'logMonitoring' && refreshInterval > 0) {
            const intervalId = setInterval(() => {
                if (logs.length > 0) {
                    const lastLogId = logs[0].id;
                    fetch(`/x/logs_after/${lastLogId}`)
                        .then(response => response.json())
                        .then(newLogs => {
                            if (newLogs.length > 1) {
                                const combinedLogs = [...newLogs.slice(1), ...logs];
                                
                                // Удаляем дубликаты и сортируем по убыванию id
                                const uniqueLogs = removeDuplicates(combinedLogs);
                                uniqueLogs.sort((a, b) => b.id - a.id);
                                
                                setLogs(uniqueLogs);
                                setLastUpdated(new Date().toISOString());
                            }
                        });
                }
            }, refreshInterval * 1000);
        
            return () => clearInterval(intervalId);
        }
    }, [logs, refreshInterval, viewMode]);

    const removeDuplicates = (logs: LogEntry[]): LogEntry[] => {
        const logMap = new Map<number, LogEntry>();
        logs.forEach(log => {
            logMap.set(log.id, log); // Записываем только уникальные по id записи
        });
        return Array.from(logMap.values());
    };

    useEffect(() => {
        const tableContainer = tableContainerRef.current;
        const tableWrapper = tableWrapperRef.current;
        const tableScrollContainer = tableScrollContainerRef.current;

        if (tableContainer && tableWrapper && tableScrollContainer) {
            const handleWheel = (event: WheelEvent) => {
                if (event.target === tableScrollContainer) {
                    tableWrapper.scrollLeft += event.deltaY;
                    event.preventDefault();
                } else {
                    tableWrapper.scrollTop += event.deltaY;
                }
            };

            tableContainer.addEventListener('wheel', handleWheel);

            return () => {
                tableContainer.removeEventListener('wheel', handleWheel);
            };
        }
    }, [logs]);

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
            const syncScroll = (source: HTMLDivElement, target: HTMLDivElement) => {
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
                        tableScrollContainer.style.left = `${tableContainer.getBoundingClientRect().left}px`; 
                        tableScrollContainer.style.width = `${tableWrapper.clientWidth}px`; 
                        tableScrollContainer.style.overflowX = 'auto'; 
                        isSticky.current = true;
                    }
                } else {
                    if (isSticky.current) {
                        tableScrollContainer.classList.remove('sticky-scroll-bar');
                        tableScrollContainer.style.position = 'relative';
                        tableScrollContainer.style.bottom = '0';
                        tableScrollContainer.style.left = '0';
                        isSticky.current = false;
                    }
                }
            };

            tableContainer.addEventListener('scroll', updateScrollBarPosition);
            updateScrollBarPosition();

            return () => {
                tableScrollContainer.removeEventListener('scroll', handleTableScrollContainerScroll);
                tableWrapper.removeEventListener('scroll', handleTableWrapperScroll);
                tableContainer.removeEventListener('scroll', updateScrollBarPosition);
            };
        }
    }, [columns, logs]);

    const handleMouseDown = (index: number, event: React.MouseEvent<HTMLDivElement>) => {
        setIsResizing(true);
        setCurrentColIndex(index);
        setStartX(event.clientX);
        setStartWidth(colWidths[index]);
    };

    const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
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
            const firstLogId = logs[logs.length - 1].id;
            fetch(`/x/logs_before/${firstLogId}`)
                .then(response => response.json())
                .then(previousLogs => {
                    if (previousLogs.length > 1) {
                        const combinedLogs = [...logs, ...previousLogs.slice(1)];
                        
                        // Удаляем дубликаты и сортируем по убыванию id
                        const uniqueLogs = removeDuplicates(combinedLogs);
                        uniqueLogs.sort((a, b) => b.id - a.id);
                        
                        setLogs(uniqueLogs);
                        setLastUpdated(new Date().toISOString());
                    }
                });
        }
    };

    const handleCellClick = (content: any, event: React.MouseEvent<HTMLDivElement>) => {
        try {
            if (!(event.target instanceof HTMLDivElement)) {
                return;
            }

            content = JSON.stringify(content);
            const cellRect = event.target.getBoundingClientRect();
            const popupWidth = 300; 
            const popupHeight = 150; 

            let leftPosition = cellRect.left + window.scrollX;
            let topPosition = cellRect.bottom + window.scrollY;

            if (leftPosition + popupWidth > window.innerWidth) {
                leftPosition = window.innerWidth - popupWidth - 10;
            }

            if (topPosition + popupHeight > window.innerHeight) {
                topPosition = cellRect.top + window.scrollY - popupHeight - 10;
            }

            setPopupContent(content);
            setPopupPosition({
                top: topPosition,
                left: leftPosition,
            });

            const handleScroll = () => {
                if (!(event.target instanceof HTMLDivElement)) {
                    return;
                }

                const updatedRect = event.target.getBoundingClientRect();
                let updatedLeftPosition = updatedRect.left + window.scrollX;
                let updatedTopPosition = updatedRect.bottom + window.scrollY;

                if (updatedLeftPosition + popupWidth > window.innerWidth) {
                    updatedLeftPosition = window.innerWidth - popupWidth - 10;
                }

                if (updatedTopPosition + popupHeight > window.innerHeight) {
                    updatedTopPosition = updatedRect.top + window.scrollY - popupHeight - 10;
                }

                setPopupPosition({
                    top: updatedTopPosition,
                    left: updatedLeftPosition,
                });
            };

            tableContainerRef.current?.addEventListener('scroll', handleScroll);

            return () => {
                tableContainerRef.current?.removeEventListener('scroll', handleScroll);
            };
        } catch (error) {
            console.error("Error in handleCellClick:", error);
        }
    };

    const handleClosePopup = () => {
        setPopupContent(null);
    };

    const handleShowLogsForIds = () => {
        let lastFetchedId: number | null = maxId; // Начинаем с максимального ID
        let allLogsFetched = false;
    
        const fetchLogsForIds = () => {
            if (minId !== null && maxId !== null && lastFetchedId !== null && !allLogsFetched) {
                const nextMinId = Math.max(minId, lastFetchedId - 10 + 1); // Рассчитываем следующий диапазон ID для запроса
    
                fetch(`/x/logs_for_ids?min_id=${nextMinId}&max_id=${lastFetchedId}`)
                    .then(response => response.json())
                    .then(newLogs => {
                        if (newLogs.length > 0) {
                            // Исключаем первую запись с заголовками, если она есть
                            const logsWithoutHeaders = newLogs.filter((log: LogEntry) => typeof log.id === 'number');
    
                            // Добавляем новые логи в конец общего массива
                            setLogs(prevLogs => [...prevLogs, ...logsWithoutHeaders].sort((a, b) => b.id - a.id));
    
                            setLastUpdated(new Date().toISOString());
    
                            // Обновляем lastFetchedId на следующий диапазон ID
                            lastFetchedId = nextMinId - 1;
    
                            // Если достигли minId, значит все данные уже загружены
                            if (lastFetchedId < minId) {
                                allLogsFetched = true;
                            } else {
                                fetchLogsForIds(); // Загружаем следующую порцию логов
                            }
                        } else {
                            allLogsFetched = true; // Останавливаем загрузку, если больше нет данных
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching logs:", error);
                        allLogsFetched = true;
                    });
            }
        };
    
        fetchLogsForIds();
    };
    
    // Обработчики для кнопок в сайдбаре
    const handleLogMonitoringClick = () => {
        setLogs([]); // Очищаем таблицу
        setViewMode('logMonitoring');
    };

    const handleSelectedPeriodClick = () => {
        setLogs([]); // Очищаем таблицу
        setViewMode('selectedPeriod');
    };

    return (
        <div className="main-content" onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
            <aside className="sidebar">
                <button onClick={handleLogMonitoringClick}>Log Monitoring</button>
                <button onClick={handleSelectedPeriodClick}>Selected Period Logs</button>
            </aside>
            <section className="content">
                {viewMode === 'logMonitoring' ? (
                    <>
                        <div className="top-bar">
                            <div className="refresh-group">
                                <label>Auto-refresh (seconds):
                                    <input
                                        type="number"
                                        min="5"
                                        step="5"
                                        value={refreshInterval}
                                        onChange={(e) => setRefreshInterval(parseInt(e.target.value, 10))}
                                    />
                                </label>
                            </div>
                            <div className="last-updated">
                                Last updated: {lastUpdated}
                            </div>
                        </div>
                        <div className="table-container" ref={tableContainerRef}>
                            <div className="table-wrapper" ref={tableWrapperRef}>
                                <LogTable
                                    logs={logs}
                                    columns={columns}
                                    colWidths={colWidths}
                                    onCellClick={handleCellClick}
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
                    </>
                ) : (
                    <>
                        <div className="top-bar">
                            <div className="refresh-group">
                                <label>Min ID:
                                    <input
                                        type="number"
                                        value={minId !== null ? minId : ''}
                                        onChange={(e) => setMinId(e.target.value ? parseInt(e.target.value, 10) : null)}
                                    />
                                </label>
                                <label>Max ID:
                                    <input
                                        type="number"
                                        value={maxId !== null ? maxId : ''}
                                        onChange={(e) => setMaxId(e.target.value ? parseInt(e.target.value, 10) : null)}
                                    />
                                </label>
                                <button onClick={handleShowLogsForIds}>Show Logs</button>
                            </div>
                            <div className="last-updated">
                                Last updated: {lastUpdated}
                            </div>
                        </div>
                        <div className="table-container" ref={tableContainerRef}>
                            <div className="table-wrapper" ref={tableWrapperRef}>
                                <LogTable
                                    logs={logs}
                                    columns={columns}
                                    colWidths={colWidths}
                                    onCellClick={handleCellClick}
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
                    </>
                )}
                {popupContent && (
                    <div
                        ref={popupRef}
                        className="popup"
                        style={{
                            position: 'absolute',
                            top: popupPosition.top,
                            left: popupPosition.left,
                            background: '#fff',
                            border: '1px solid #ccc',
                            padding: '10px',
                            zIndex: 1000,
                            maxWidth: '300px',
                            overflow: 'auto',
                        }}
                    >
                        <button onClick={handleClosePopup}>Close</button>
                        <div>{popupContent}</div>
                    </div>
                )}
            </section>
        </div>
    );
};

export default MainContent;

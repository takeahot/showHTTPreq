import React, { useState, useEffect, useRef } from 'react';
import LogTable from './LogTable';
import './MainContent.css';

interface LogEntry {
    id: number;
    [key: string]: any; // Для остальных полей, которые могут быть в объекте
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
    const [refreshInterval, setRefreshInterval] = useState<number>(30);
    const [popupContent, setPopupContent] = useState<string | null>(null);
    const [popupPosition, setPopupPosition] = useState<PopupPosition>({ top: 0, left: 0 });

    const tableRef = useRef<HTMLDivElement | null>(null);
    const tableScrollBarRef = useRef<HTMLDivElement | null>(null);
    const tableScrollContainerRef = useRef<HTMLDivElement | null>(null);
    const tableWrapperRef = useRef<HTMLDivElement | null>(null);
    const tableContainerRef = useRef<HTMLDivElement | null>(null);
    const bottomBarRef = useRef<HTMLDivElement | null>(null);
    const popupRef = useRef<HTMLDivElement | null>(null);
    const isSticky = useRef<boolean>(false);

    useEffect(() => {
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
                const lastLogId = logs[0].id;
                fetch(`/logs_after/${lastLogId}`)
                    .then(response => response.json())
                    .then(newLogs => {
                        if (newLogs.length > 1) {
                            setLogs(prevLogs => [...newLogs.slice(1), ...prevLogs]);
                        }
                    });
            }
        }, refreshInterval * 1000);
    
        return () => clearInterval(intervalId);
    }, [logs, refreshInterval]);

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
            fetch(`/logs_before/${firstLogId}`)
                .then(response => response.json())
                .then(previousLogs => {
                    if (previousLogs.length > 1) {
                        setLogs(prevLogs => [...prevLogs, ...previousLogs.slice(1)]);
                    }
                });
        }
    };

    const handleCellClick = (content: any, event: React.MouseEvent<HTMLDivElement>) => {
        try {
            // Проверяем, является ли target HTMLDivElement
            if (!(event.target instanceof HTMLDivElement)) {
                return;
            }

            content = JSON.stringify(content);
            console.log("Clicked content:", content);
            console.log("Event target:", event.target);
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
                // Проверяем, является ли target HTMLDivElement
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
                                onChange={(e) => setRefreshInterval(parseInt(e.target.value, 10))}
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

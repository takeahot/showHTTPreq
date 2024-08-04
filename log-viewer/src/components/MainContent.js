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
    const [popupContent, setPopupContent] = useState(null);
    const [popupPosition, setPopupPosition] = useState({ top: 0, left: 0 });

    const tableRef = useRef(null);
    const tableScrollBarRef = useRef(null);
    const tableScrollContainerRef = useRef(null);
    const tableWrapperRef = useRef(null);
    const tableContainerRef = useRef(null);
    const bottomBarRef = useRef(null);
    const isSticky = useRef(false);
    const popupRef = useRef(null); // Ref для всплывающего окна

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
                const lastLogId = logs[0].id; // Используем id самого верхнего лога в таблице
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
        const updateScrollBarWidth = () => {
            if (tableRef.current && tableScrollBarRef.current) {
                const tableWidth = tableRef.current.scrollWidth; // Ширина всей таблицы
                tableScrollBarRef.current.style.width = `${tableWidth}px`;
            }
        };

        updateScrollBarWidth();

        const tableScrollContainer = tableScrollContainerRef.current;
        const tableWrapper = tableWrapperRef.current;
        const tableContainer = tableContainerRef.current;

        if (tableScrollContainer && tableWrapper && tableContainer) {
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
                        tableScrollContainer.style.left = `${tableContainer.getBoundingClientRect().left}px`;  // Установим левое смещение полосы прокрутки относительно контейнера
                        tableScrollContainer.style.width = `${tableWrapper.clientWidth}px`; // Ограничиваем ширину полосы прокрутки
                        tableScrollContainer.style.overflowX = 'auto'; // Чтобы полоска могла прокручиваться
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
            const firstLogId = logs[logs.length - 1].id; // Используем id самого нижнего лога в таблице
            fetch(`/logs_before/${firstLogId}`)
                .then(response => response.json())
                .then(previousLogs => {
                    if (previousLogs.length > 1) {
                        setLogs(prevLogs => [...prevLogs, ...previousLogs.slice(1)]);
                    }
                });
        }
    };

    const handleCellClick = (content, event) => {
        const cellRect = event.target.getBoundingClientRect();
        const popupWidth = 300; // Предполагаемая ширина всплывающего окна
        const popupHeight = 150; // Предполагаемая высота всплывающего окна

        let leftPosition = cellRect.left + window.scrollX;
        let topPosition = cellRect.bottom + window.scrollY;

        // Проверка, не выходит ли всплывающее окно за границы экрана
        if (leftPosition + popupWidth > window.innerWidth) {
            leftPosition = window.innerWidth - popupWidth - 10; // Сдвиг влево
        }

        if (topPosition + popupHeight > window.innerHeight) {
            topPosition = cellRect.top + window.scrollY - popupHeight - 10; // Сдвиг вверх
        }

        setPopupContent(content);
        setPopupPosition({
            top: topPosition,
            left: leftPosition,
        });

        // Обновляем позицию при каждом скролле таблицы
        const handleScroll = () => {
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

        tableContainerRef.current.addEventListener('scroll', handleScroll);

        // Удаление обработчика событий при закрытии popup
        return () => {
            tableContainerRef.current.removeEventListener('scroll', handleScroll);
        };
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

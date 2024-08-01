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
    const bottomBarRef = useRef(null);

    useEffect(() => {
        fetch('/exampleData.json')
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
        const updateScrollBarWidth = () => {
            if (tableRef.current && tableScrollBarRef.current) {
                const tableWidth = tableRef.current.scrollWidth;
                tableScrollBarRef.current.style.width = `${tableWidth}px`;
            }
        };

        updateScrollBarWidth();

        const tableScrollContainer = tableScrollContainerRef.current;
        const tableWrapper = tableWrapperRef.current;
        const bottomBar = bottomBarRef.current;

        if (tableScrollContainer && tableWrapper && bottomBar) {
            const syncScroll = (source, target) => {
                target.scrollLeft = source.scrollLeft;
            };

            const handleTableScrollContainerScroll = () => syncScroll(tableScrollContainer, tableWrapper);
            const handleTableWrapperScroll = () => syncScroll(tableWrapper, tableScrollContainer);

            tableScrollContainer.addEventListener('scroll', handleTableScrollContainerScroll);
            tableWrapper.addEventListener('scroll', handleTableWrapperScroll);

            const updateScrollBarPosition = () => {
                const scrollBarBottom = tableScrollContainer.getBoundingClientRect().bottom;
                const footerTop = bottomBar.getBoundingClientRect().top;

                if (scrollBarBottom >= footerTop) {
                    tableScrollContainer.classList.add('sticky-scroll-bar');
                } else {
                    tableScrollContainer.classList.remove('sticky-scroll-bar');
                }
            };

            window.addEventListener('scroll', updateScrollBarPosition);

            return () => {
                tableScrollContainer.removeEventListener('scroll', handleTableScrollContainerScroll);
                tableWrapper.removeEventListener('scroll', handleTableWrapperScroll);
                window.removeEventListener('scroll', updateScrollBarPosition);
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
        // Логика для загрузки дополнительных строк
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
                <div className="table-container">
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

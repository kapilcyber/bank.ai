import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const IndiaChoropleth = ({ data }) => {
    const [hoveredState, setHoveredState] = useState(null);
    const [selectedState, setSelectedState] = useState(null);

    // Standard high-quality state paths for India
    const INDIA_STATES_PATHS = [
        { id: 'AN', name: 'Andaman and Nicobar Islands', d: 'M576,649l-11,23l6,14l-11,23l25-10l-1-29L576,649z M596,750l-8,24l22,1l-2-21L596,750z M606,812l-10,23l22,2l-2-23L606,812z' },
        { id: 'AP', name: 'Andhra Pradesh', d: 'M302,572l-15,10l-37,4l-11,17l19,40l3,33l26,17l36,2l19,25l24-11l-5-29l25-19l-9-26l32-15l-19-48l-23-9l-26,5L302,572z M353,493l-17-10l-16,14l7,24l40,19l18-18L353,493z' },
        { id: 'AR', name: 'Arunachal Pradesh', d: 'M601,232l-13,8l-25-34l-13,6l10,39l-14,31l26,16l19-14l33,26l22-10l12-34l-11-23L601,232z' },
        { id: 'AS', name: 'Assam', d: 'M537,276l-20,3l-2,32l53,4l2,19l31,3l1-28l-26-17L537,276z M509,343l-13,4l-4,28l46,3L509,343z M546,358l-15,1l-2,23l29-2l2,19l26-12l-13-14L546,358z' },
        { id: 'BR', name: 'Bihar', d: 'M397,294l-37,3l-3,21l33,35l29,0l40,17l8-22l-23-28l-12-25L397,294z' },
        { id: 'CH', name: 'Chandigarh', d: 'M199,141l-4,6l4,5l4-5L199,141z' },
        { id: 'CT', name: 'Chhattisgarh', d: 'M314,357l-14,24l2,47l19,30l6,55l32-1l-5-53l25-13l-4-41l-25-24l-34-19L314,357z' },
        { id: 'DN', name: 'Dadra and Nagar Haveli', d: 'M145,466l-5,7l6,4l3-6L145,466z' },
        { id: 'DD', name: 'Daman and Diu', d: 'M136,441l-5,5h6L136,441z M107,445l-4,4h6L107,445z' },
        { id: 'DL', name: 'Delhi', d: 'M198,228l-6,7l6,7l7-6L198,228z' },
        { id: 'GA', name: 'Goa', d: 'M157,595l-7,7l6,14l11-6l-2-10L157,595z' },
        { id: 'GJ', name: 'Gujarat', d: 'M130,361l-36,5l-21,43l37,18l0,28l40,11l25-23l25-2l6-43l-37-14l-25-10L130,361z M51,364l-11,10l19,26l23-21L51,364z' },
        { id: 'HR', name: 'Haryana', d: 'M201,173l-18,17l-13,40l19,25l25,0l12-16l-3-26l26-16l-3-12l-24-11L201,173z' },
        { id: 'HP', name: 'Himachal Pradesh', d: 'M191,85l-11,26l11,35l25,12l26-1l14-31l-34-29l-13,1L191,85z' },
        { id: 'JK', name: 'Jammu and Kashmir', d: 'M179,0l-14,31l13,34l19,21l32,3l41-26l11-57l-47-23l-28,9L179,0z' },
        { id: 'JH', name: 'Jharkhand', d: 'M385,341l-35,3l-2,23l62,4l31-2l5-24l-20-19L385,341z' },
        { id: 'KA', name: 'Karnataka', d: 'M161,541l-14,39l10,37l25,55l31,24l13-26l-11-55l32-16l3-55l-33-33l-31,2L161,541z' },
        { id: 'KL', name: 'Kerala', d: 'M217,705l-5,50l26,45l11-4l-11-37l-6-52L217,705z' },
        { id: 'LA', name: 'Ladakh', d: 'M230,12l10,51l47,21l16-32l-25-30L230,12z' },
        { id: 'LD', name: 'Lakshadweep', d: 'M115,750l-3,7l7,1l-0-6L115,750z M125,780l-4,6l7,2l0-7L125,780z M140,845l-4,6l8,2l0-8L140,845z' },
        { id: 'MP', name: 'Madhya Pradesh', d: 'M177,330l-14,24l25,48l47,1l19,16l61-5l28-36l-2-29l25-12l-18-24l-53,1l-25-14l-48,4l-25-12L177,330z' },
        { id: 'MH', name: 'Maharashtra', d: 'M153,446l-14,14l7,41l15,35l36,7l31,19l33,3l50-32l-14-32l16-29l-36-32l-47,1l-26-26l-25,1L153,446z' },
        { id: 'MN', name: 'Manipur', d: 'M573,347l-13,12l6,19l23,1l0-23L573,347z' },
        { id: 'ML', name: 'Meghalaya', d: 'M503,322l-14,21l47,1l12-16L503,322z' },
        { id: 'MZ', name: 'Mizoram', d: 'M562,374l-11,10l2,26l22,1l0-29L562,374z' },
        { id: 'NL', name: 'Nagaland', d: 'M583,277l-13,10l6,21l22-6l-2-21L583,277z' },
        { id: 'OR', name: 'Odisha', d: 'M358,409l-13,29l41,40l45-1l4-28l-25-24l-31,2l-6-16L358,409z' },
        { id: 'PY', name: 'Puducherry', d: 'M302,698l-5,5h7L302,698z M271,788l-4,4h6L271,788z M265,745l-4,4h6L265,745z' },
        { id: 'PB', name: 'Punjab', d: 'M188,103l-19,10l-14,41l28,21l21-1l9-39l-11-25L188,103z' },
        { id: 'RJ', name: 'Rajasthan', d: 'M141,180l-45,71l14,35l25,12l48-1l24,25l19-14l0-32l11-47l-35-13l-14-25L141,180z' },
        { id: 'SK', name: 'Sikkim', d: 'M457,252l-10,14l22,6l-1-18L457,252z' },
        { id: 'TN', name: 'Tamil Nadu', d: 'M217,748l13,41l25,44l29,0l32-47l-9-33l-24-11l-36,5L217,748z' },
        { id: 'TG', name: 'Telangana', d: 'M265,510l-17,10l19,40l31,24l53-23l-3-33l-36-31L265,510z' },
        { id: 'TR', name: 'Tripura', d: 'M546,381l-11,5l2,14l20-1l-1-16L546,381z' },
        { id: 'UP', name: 'Uttar Pradesh', d: 'M234,228l-18,24l25,48l61-5l28-36l3-12l37-4l2-23l-35-37l-47,1l-19,12l-25-14L234,228z' },
        { id: 'UT', name: 'Uttarakhand', d: 'M255,164l-14,31l33,26l22-10l-12-32L255,164z' },
        { id: 'WB', name: 'West Bengal', d: 'M441,273l-13,63l25,31l13-25l-11-17L441,273z M446,419l-11,21l32,1l0-21L446,419z' }
    ];

    const chartData = useMemo(() => {
        // High-end Dashboard Palette: Deep Slate to Cyber Gold
        const getColorScale = (count) => {
            if (count === 0) return '#0f172a'; // Deep Navy
            if (count < 5) return '#0ea5e9';   // Sky Blue
            if (count < 15) return '#10b981';  // Emerald
            if (count < 30) return '#f59e0b';  // Amber
            return '#f43f5e';                 // Rose
        };

        return INDIA_STATES_PATHS.map((state) => {
            const stateData = data.find(d =>
                d.state.toLowerCase().includes(state.name.toLowerCase()) ||
                state.name.toLowerCase().includes(d.state.toLowerCase())
            );
            const count = stateData ? stateData.count : 0;
            return {
                ...state,
                count,
                fill: getColorScale(count),
                isActive: count > 0
            };
        });
    }, [data]);

    const activeFocus = useMemo(() => selectedState || hoveredState, [selectedState, hoveredState]);
    const focusData = useMemo(() => {
        if (!activeFocus) return null;
        return data.find(d =>
            d.state.toLowerCase().includes(activeFocus.name.toLowerCase()) ||
            activeFocus.name.toLowerCase().includes(d.state.toLowerCase())
        ) || { count: 0, state: activeFocus.name };
    }, [activeFocus, data]);

    return (
        <div className="premium-india-dashboard">
            {/* Header with KPI Ribbons */}
            <div className="dashboard-hud-header">
                <div className="hud-title-group">
                    <h2>Geospatial Talent Intelligence</h2>
                    <p>India Regional Distribution Analysis</p>
                </div>
                <div className="hud-stats-ribbon">
                    <div className="ribbon-stat">
                        <span className="label">Total Hubs</span>
                        <span className="value">{data.length}</span>
                    </div>
                    <div className="ribbon-stat">
                        <span className="label">Leading Region</span>
                        <span className="value">
                            {[...data].sort((a, b) => b.count - a.count)[0]?.state || 'N/A'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="dashboard-main-content">
                {/* Left: Interactive Map HUD */}
                <div className="map-hud-container">
                    <div className="map-frame">
                        <svg viewBox="0 0 650 900">
                            <defs>
                                <filter id="hud-glow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="3" result="blur" />
                                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                                </filter>
                                <radialGradient id="map-grad" cx="50%" cy="50%" r="50%">
                                    <stop offset="0%" stopColor="rgba(0, 242, 255, 0.05)" />
                                    <stop offset="100%" stopColor="transparent" />
                                </radialGradient>
                            </defs>

                            {/* Background Atmosphere */}
                            <circle cx="325" cy="450" r="400" fill="url(#map-grad)" />

                            {/* State Layers */}
                            {chartData.map((state) => {
                                const isSelected = selectedState?.id === state.id;
                                const isHovered = hoveredState?.id === state.id;
                                const isDimmed = activeFocus && !isSelected && !isHovered;

                                return (
                                    <motion.path
                                        key={state.id}
                                        d={state.d}
                                        initial={false}
                                        animate={{
                                            fill: isSelected || isHovered ? '#fff' : state.fill,
                                            fillOpacity: isDimmed ? 0.2 : 1,
                                            stroke: isSelected || isHovered ? '#fff' : 'rgba(255,255,255,0.1)',
                                            strokeWidth: isSelected || isHovered ? 2 : 0.8,
                                            scale: isSelected || isHovered ? 1.02 : 1
                                        }}
                                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                        onMouseEnter={() => setHoveredState(state)}
                                        onMouseLeave={() => setHoveredState(null)}
                                        onClick={() => setSelectedState(isSelected ? null : state)}
                                        style={{
                                            cursor: 'pointer',
                                            filter: isSelected || isHovered ? 'url(#hud-glow)' : 'none'
                                        }}
                                    />
                                );
                            })}
                        </svg>

                        {/* Map HUD Labels */}
                        <div className="map-hud-legend">
                            {[
                                { color: '#0f172a', label: 'Empty' },
                                { color: '#0ea5e9', label: '1-5' },
                                { color: '#10b981', label: '6-15' },
                                { color: '#f59e0b', label: '16-30' },
                                { color: '#f43f5e', label: '31+' }
                            ].map(l => (
                                <div key={l.label} className="legend-item">
                                    <span className="dot" style={{ background: l.color }}></span>
                                    <span className="text">{l.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Data Analysis HUD */}
                <div className="analysis-hud-container">
                    <AnimatePresence mode="wait">
                        {activeFocus ? (
                            <motion.div
                                key={activeFocus.id}
                                className="focus-hud-card"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                            >
                                <div className="card-header">
                                    <div className="region-indicator" style={{ background: activeFocus.fill }}></div>
                                    <div className="header-meta">
                                        <h3>{activeFocus.name}</h3>
                                        <span className="coord-text">REGION_CODE: {activeFocus.id}</span>
                                    </div>
                                </div>

                                <div className="metrics-grid">
                                    <div className="metric-box">
                                        <span className="m-label">CANDIDATES</span>
                                        <span className="m-value">{focusData.count}</span>
                                        <div className="m-bar"><div className="m-fill" style={{ width: `${Math.min(focusData.count * 3, 100)}%`, background: activeFocus.fill }}></div></div>
                                    </div>
                                    <div className="metric-box">
                                        <span className="m-label">MARKET SHARE</span>
                                        <span className="m-value">{((focusData.count / (data.reduce((a, b) => a + b.count, 0) || 1)) * 100).toFixed(1)}%</span>
                                    </div>
                                </div>

                                <div className="action-bureau">
                                    <button className="hud-action-btn" onClick={() => setSelectedState(null)}>
                                        DISMISS_FOCUS
                                    </button>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div className="empty-hud-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <div className="hud-logo-anim">🎯</div>
                                <h3>SYSTEM_READY</h3>
                                <p>Select a region on the global map to initialize localized data streams and talent analysis.</p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Top 5 Locations List */}
                    <div className="ranking-hud">
                        <h4 className="ranking-title">TOP_TALENT_HUBS</h4>
                        <div className="ranking-list">
                            {[...data].sort((a, b) => b.count - a.count).slice(0, 5).map((loc, i) => (
                                <div key={i} className="ranking-item">
                                    <span className="rank-num">0{i + 1}</span>
                                    <span className="rank-name">{loc.state}</span>
                                    <span className="rank-count">{loc.count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default IndiaChoropleth;

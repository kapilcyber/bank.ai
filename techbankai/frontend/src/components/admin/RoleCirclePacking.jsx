import React, { useMemo, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const RoleCirclePacking = ({ data, selectedRole, onRoleClick, onNavigateToRecords }) => {
    const [hoveredRole, setHoveredRole] = useState(null);
    const containerRef = useRef(null);

    const packedData = useMemo(() => {
        if (!data || data.length === 0) return [];

        const sortedData = [...data]
            .sort((a, b) => b.count - a.count)
            .slice(0, 25);

        const maxCount = Math.max(...sortedData.map(d => d.count), 1);
        const minRadius = 45;
        const maxRadius = 110;

        const colors = ['#06b6d4', '#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#6366f1'];

        return sortedData.map((item, index) => {
            const radius = minRadius + (item.count / maxCount) * (maxRadius - minRadius);
            const angle = index * 137.5;
            const distance = Math.sqrt(index) * 65;
            const x = 500 + Math.cos(angle * (Math.PI / 180)) * distance;
            const y = 400 + Math.sin(angle * (Math.PI / 180)) * distance;

            return {
                ...item,
                x,
                y,
                radius,
                fill: colors[index % colors.length]
            };
        });
    }, [data]);

    // Role to display in the side info panel: Selected role takes priority, then hovered role
    const displayRole = useMemo(() => {
        if (selectedRole) {
            return packedData.find(d => d.role === selectedRole);
        }
        return hoveredRole;
    }, [selectedRole, hoveredRole, packedData]);

    const viewBox = useMemo(() => {
        if (!selectedRole) return "0 0 1000 800";
        const target = packedData.find(d => d.role === selectedRole);
        if (!target) return "0 0 1000 800";
        // Reduced zoom intensity: increase zoomSize (buffer around the target)
        const zoomSize = target.radius * 8;
        return `${target.x - zoomSize / 2} ${target.y - zoomSize / 2} ${zoomSize} ${zoomSize}`;
    }, [selectedRole, packedData]);

    // Close tooltip only if clicking outside
    useEffect(() => {
        const handleGlobalClick = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                // If clicking outside, clear both selection and hover
                if (onRoleClick) onRoleClick(null);
                setHoveredRole(null);
            }
        };
        window.addEventListener('mousedown', handleGlobalClick);
        return () => window.removeEventListener('mousedown', handleGlobalClick);
    }, [onRoleClick]);

    if (!data || data.length === 0) {
        return <div className="no-data-placeholder"><p>No role data available</p></div>;
    }

    return (
        <div
            ref={containerRef}
            className="circle-packing-wrapper"
            style={{
                position: 'relative',
                cursor: 'default',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'center',
                gap: '20px',
                padding: '20px'
            }}
        >
            {/* Left Side: The Chart */}
            <div style={{ flex: '1', position: 'relative', maxWidth: '1000px' }}>
                <motion.svg
                    viewBox={viewBox}
                    className="circle-packing-svg"
                    initial={false}
                    animate={{ viewBox }}
                    transition={{ type: "spring", stiffness: 80, damping: 20 }}
                    style={{ overflow: 'visible', width: '100%', height: 'auto' }}
                >
                    <defs>
                        <filter id="solid-glow" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="3" result="glow" />
                            <feMerge><feMergeNode in="glow" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                    </defs>

                    {packedData.map((item, i) => {
                        const isSelected = selectedRole === item.role;
                        const isHovered = hoveredRole?.role === item.role;
                        const isDimmed = selectedRole ? !isSelected : (hoveredRole ? !isHovered : false);

                        return (
                            <motion.g
                                key={i}
                                initial={{ opacity: 0, scale: 0 }}
                                animate={{
                                    opacity: isDimmed ? 0.2 : 1,
                                    scale: isSelected || isHovered ? 1.15 : 1
                                }}
                                transition={{ duration: 0.4, delay: i * 0.03 }}
                                whileHover={{ scale: 1.1, zIndex: 10 }}
                                onMouseEnter={() => setHoveredRole(item)}
                                onMouseLeave={() => setHoveredRole(null)}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onRoleClick(item.role === selectedRole ? null : item.role);
                                }}
                                style={{ cursor: 'pointer' }}
                            >
                                <circle
                                    cx={item.x}
                                    cy={item.y}
                                    r={item.radius}
                                    fill={item.fill}
                                    fillOpacity={1}
                                    stroke="rgba(255,255,255,0.2)"
                                    strokeWidth={isSelected || isHovered ? 3 : 1}
                                    style={{ filter: isSelected || isHovered ? 'url(#solid-glow)' : 'none' }}
                                />
                                <text
                                    x={item.x}
                                    y={item.y - 8}
                                    textAnchor="middle"
                                    fill="#fff"
                                    fontSize={isSelected || isHovered ? "16px" : (item.radius > 60 ? "12px" : "10px")}
                                    fontWeight="800"
                                    style={{ pointerEvents: 'none', textShadow: '0 0 10px rgba(0,0,0,0.5)' }}
                                >
                                    {item.role.length > 20 ? item.role.substring(0, 17) + '...' : item.role}
                                </text>
                                <text
                                    x={item.x}
                                    y={item.y + 18}
                                    textAnchor="middle"
                                    fill="#fff"
                                    fontSize={isSelected || isHovered ? "22px" : (item.radius > 60 ? "16px" : "12px")}
                                    fontWeight="900"
                                    style={{ pointerEvents: 'none', textShadow: '0 0 8px rgba(0,0,0,0.3)' }}
                                >
                                    {item.count}
                                </text>
                            </motion.g>
                        );
                    })}
                </motion.svg>
            </div>

            {/* Right Side: Role Details (Unified for Selection and Hover) */}
            <div style={{ width: '300px', flexShrink: 0, marginTop: '50px' }}>
                <AnimatePresence mode="wait">
                    {displayRole ? (
                        <motion.div
                            key={displayRole.role}
                            className="role-analysis-panel"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            style={{ borderLeftColor: displayRole.fill }}
                        >
                            <div className="panel-header-new">
                                <div className="header-main">
                                    <span className="role-title" style={{ color: displayRole.fill }}>{displayRole.role}</span>
                                    {selectedRole === displayRole.role && (
                                        <span className="selection-badge" style={{ background: displayRole.fill }}>Selected</span>
                                    )}
                                </div>
                                <div className="header-meta">
                                    <span className="talent-count">Total Cluster: <strong>{displayRole.count} Professionals</strong></span>
                                </div>
                            </div>

                            <div className="talent-snapshot-section">
                                <label className="snapshot-title">Market Talent Preview</label>
                                <div className="talent-list-container">
                                    {(displayRole.candidates || []).slice(0, 5).map((cand, idx) => (
                                        <div key={idx} className="talent-row-new">
                                            <div className="talent-info-main">
                                                <span className="talent-name">{cand.name}</span>
                                                <span className="talent-experience">{cand.exp.toFixed(1)} Yrs Exp</span>
                                            </div>
                                            <div className="talent-status-dot" style={{ background: displayRole.fill }} />
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <button
                                className="panel-action-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onNavigateToRecords(displayRole.role);
                                }}
                                style={{
                                    background: `linear-gradient(90deg, ${displayRole.fill} 0%, ${displayRole.fill}cc 100%)`,
                                    boxShadow: `0 4px 15px ${displayRole.fill}44`
                                }}
                            >
                                {displayRole.count > 5 ? `Analyze Complete ${displayRole.count} Talent Set` : 'View Detailed Records'}
                            </button>
                        </motion.div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            style={{
                                color: '#64748b',
                                textAlign: 'center',
                                padding: '40px 20px',
                                border: '1px dashed rgba(255,255,255,0.1)',
                                borderRadius: '12px',
                                background: 'rgba(0,0,0,0.2)'
                            }}
                        >
                            <p style={{ fontSize: '0.9rem', marginBottom: '10px' }}>Use the filter or select a cluster to view distribution</p>
                            <div style={{ fontSize: '2rem', opacity: 0.3 }}>🎯</div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default RoleCirclePacking;

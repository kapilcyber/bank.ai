import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AdminTransition.css';

const AdminTransition = ({ onComplete }) => {
    const [stage, setStage] = useState(0);
    const [terminalLogs, setTerminalLogs] = useState([]);

    const stages = [
        "Establishing Secure Connection...",
        "Verifying Admin Credentials...",
        "Scanning Security Protocols...",
        "Syncing Neural Networks...",
        "Access Granted. Welcome Admin."
    ];

    useEffect(() => {
        const timer = setInterval(() => {
            setStage((prev) => (prev < stages.length - 1 ? prev + 1 : prev));
        }, 1000);

        const completeTimer = setTimeout(() => {
            onComplete();
        }, 5500);

        const logInterval = setInterval(() => {
            const prefixes = ['[INFO]', '[SYS]', '[SEC]', '[AUTH]'];
            const actions = ['Accessing', 'Scanning', 'Loading', 'Verifying'];
            const targets = ['Mainframe', 'Database', 'Protocols', 'Encrypted_DB'];
            const newLog = `${prefixes[Math.floor(Math.random() * prefixes.length)]} ${actions[Math.floor(Math.random() * actions.length)]} ${targets[Math.floor(Math.random() * targets.length)]}...`;
            setTerminalLogs(prev => [...prev.slice(-10), newLog]);
        }, 400);

        return () => {
            clearInterval(timer);
            clearInterval(logInterval);
            clearTimeout(completeTimer);
        };
    }, [onComplete, stages.length]);

    return (
        <div className="admin-transition-overlay">
            <div className="video-background">
                <div className="scanline"></div>
                <div className="noise"></div>
            </div>

            <div className="content-wrapper">
                <motion.div
                    className="hexagon-container"
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                >
                    <div className="hexagon">
                        <div className="hexagon-inner">
                            <motion.span
                                className="tech-logo-text"
                                animate={{ opacity: [0.5, 1, 0.5] }}
                                transition={{ repeat: Infinity, duration: 2 }}
                            >
                                TB
                            </motion.span>
                        </div>
                    </div>
                    <motion.div
                        className="outer-ring"
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
                    ></motion.div>
                    <motion.div
                        className="outer-ring-dashed"
                        animate={{ rotate: -360 }}
                        transition={{ repeat: Infinity, duration: 12, ease: "linear" }}
                    ></motion.div>
                </motion.div>

                <div className="status-container">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={stage}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="status-text"
                        >
                            {stages[stage]}
                        </motion.div>
                    </AnimatePresence>

                    <div className="progress-bar-container">
                        <motion.div
                            className="progress-bar-fill"
                            initial={{ width: "0%" }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 5, ease: "linear" }}
                        />
                    </div>
                </div>

                <div className="floating-terminal">
                    {terminalLogs.map((log, i) => (
                        <div key={i} className="terminal-line">{log}</div>
                    ))}
                </div>

                <div className="binary-rain">
                    {[...Array(20)].map((_, i) => (
                        <motion.div
                            key={i}
                            className="binary-column"
                            initial={{ y: -100 }}
                            animate={{ y: 1000 }}
                            transition={{
                                duration: Math.random() * 2 + 1,
                                repeat: Infinity,
                                delay: Math.random() * 2,
                                ease: "linear"
                            }}
                        >
                            {Math.random() > 0.5 ? '1' : '0'}
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default AdminTransition;

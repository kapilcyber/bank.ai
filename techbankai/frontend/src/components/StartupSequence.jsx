import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './StartupSequence.css';

const StartupSequence = ({ onComplete }) => {
    const [phase, setPhase] = useState(0);

    useEffect(() => {
        // Sequence phases
        const timers = [
            setTimeout(() => setPhase(1), 1000), // Logo Draw
            setTimeout(() => setPhase(2), 2500), // Text Reveal
            setTimeout(() => setPhase(3), 4000), // Final Glow
            setTimeout(() => onComplete(), 5000), // Fade to Login
        ];

        return () => timers.forEach(clearTimeout);
    }, [onComplete]);

    return (
        <div className="startup-container">
            <div className="background-grid"></div>

            <AnimatePresence>
                {phase < 4 && (
                    <motion.div
                        className="startup-content"
                        exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
                        transition={{ duration: 1 }}
                    >
                        {/* Central Logo Assembly */}
                        <div className="logo-assembly">
                            <motion.svg
                                width="200"
                                height="200"
                                viewBox="0 0 100 100"
                                initial="hidden"
                                animate="visible"
                            >
                                {/* Circuit lines */}
                                <motion.path
                                    d="M 10 50 L 30 50 L 40 30 L 60 70 L 70 50 L 90 50"
                                    fill="transparent"
                                    stroke="#4f46e5"
                                    strokeWidth="2"
                                    variants={{
                                        hidden: { pathLength: 0, opacity: 0 },
                                        visible: {
                                            pathLength: 1,
                                            opacity: 1,
                                            transition: { duration: 2, ease: "easeInOut" }
                                        }
                                    }}
                                />

                                {/* Hexagon outline */}
                                <motion.path
                                    d="M 50 10 L 85 30 L 85 70 L 50 90 L 15 70 L 15 30 Z"
                                    fill="transparent"
                                    stroke="#00d4ff"
                                    strokeWidth="1"
                                    variants={{
                                        hidden: { pathLength: 0, opacity: 0 },
                                        visible: {
                                            pathLength: 1,
                                            opacity: [0, 1, 0.5, 1],
                                            transition: { duration: 1.5, delay: 0.5 }
                                        }
                                    }}
                                />
                            </motion.svg>

                            <motion.div
                                className="logo-text-glitch"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: phase >= 2 ? 1 : 0 }}
                            >
                                <span className="glitch-text" data-text="TECHBANK.AI">TECHBANK.AI</span>
                            </motion.div>
                        </div>

                        {/* Status Indicators */}
                        <div className="startup-footer">
                            <motion.div
                                className="loading-bar-container"
                                initial={{ width: 0 }}
                                animate={{ width: 300 }}
                                transition={{ duration: 4, ease: "linear" }}
                            >
                                <div className="loading-bar-fill"></div>
                            </motion.div>
                            <motion.div
                                className="status-messages"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                            >
                                {phase === 0 && <span>Initializing Core Systems...</span>}
                                {phase === 1 && <span>Syncing Cyber-Auth Protocols...</span>}
                                {phase === 2 && <span>Establishing Secure Tunnel...</span>}
                                {phase === 3 && <span>System Ready.</span>}
                            </motion.div>
                        </div>

                        {/* Decorative scanning line */}
                        <motion.div
                            className="scan-line"
                            animate={{ top: ['0%', '100%', '0%'] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                        />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Background binary rain effect */}
            <div className="rain-container">
                {[...Array(15)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="rain-column"
                        initial={{ y: -100, opacity: 0 }}
                        animate={{ y: '100vh', opacity: [0, 1, 0] }}
                        transition={{
                            duration: 2 + Math.random() * 2,
                            repeat: Infinity,
                            delay: Math.random() * 3,
                            ease: "linear"
                        }}
                    >
                        {Array.from({ length: 10 }).map((_, j) => (
                            <div key={j}>{Math.floor(Math.random() * 2)}</div>
                        ))}
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default StartupSequence;

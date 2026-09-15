const LEVELS = ['debug', 'info', 'warn', 'error'];

function log(level, message, meta) {
    const entry = { level, message, ...(meta ? { meta } : {}) };
    const line = JSON.stringify(entry);
    if (level === 'error') {
        console.error(line);
    } else if (level === 'warn') {
        console.warn(line);
    } else {
        console.log(line);
    }
}

const logger = {};
for (const level of LEVELS) {
    logger[level] = (message, meta) => log(level, message, meta);
}

module.exports = logger;

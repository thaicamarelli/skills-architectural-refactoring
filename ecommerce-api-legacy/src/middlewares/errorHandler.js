const logger = require('../services/loggerService');

class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    logger.error('request.error', { status, message: err.message });
    res.status(status).json({ error: status === 500 ? 'Erro interno' : err.message });
}

module.exports = { HttpError, notFoundHandler, errorHandler };

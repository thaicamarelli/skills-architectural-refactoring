const settings = require('../config/settings');

// Protege rotas administrativas/destrutivas que antes não tinham nenhuma verificação
// (ver findings CRITICAL "Endpoint destrutivo sem autenticação" e MEDIUM "Ausência de
// autenticação/autorização em endpoint admin" no relatório de auditoria).
function requireAdmin(req, res, next) {
    const providedKey = req.get('x-admin-key');

    if (!providedKey || providedKey !== settings.adminApiKey) {
        return res.status(401).json({ error: 'Não autorizado' });
    }

    next();
}

module.exports = requireAdmin;

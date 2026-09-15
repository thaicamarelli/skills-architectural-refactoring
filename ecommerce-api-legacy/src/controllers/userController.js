function makeUserController({ userModel }) {
    return {
        async deleteUser(req, res) {
            await userModel.deleteCascade(req.params.id);
            res.send('Usuário e registros dependentes (matrículas e pagamentos) removidos.');
        },
    };
}

module.exports = makeUserController;

class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return lastID;
    }

    exists(id) {
        return this.db.get('SELECT id FROM users WHERE id = ?', [id]);
    }

    // Remove o usuário e todos os registros dependentes (matrículas e pagamentos) em uma
    // única transação, evitando os órfãos deixados pela versão anterior do endpoint.
    async deleteCascade(id) {
        return this.db.transaction(async (db) => {
            const enrollments = await db.all('SELECT id FROM enrollments WHERE user_id = ?', [id]);
            const enrollmentIds = enrollments.map((e) => e.id);

            for (const enrollmentId of enrollmentIds) {
                await db.run('DELETE FROM payments WHERE enrollment_id = ?', [enrollmentId]);
            }
            await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes > 0;
        });
    }
}

module.exports = UserModel;

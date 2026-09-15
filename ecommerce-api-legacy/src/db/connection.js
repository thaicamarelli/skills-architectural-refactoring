const sqlite3 = require('sqlite3').verbose();

class Database {
    constructor(filename) {
        this.raw = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        const db = this.raw;
        return new Promise((resolve, reject) => {
            db.run(sql, params, function callback(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        const db = this.raw;
        return new Promise((resolve, reject) => {
            db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        const db = this.raw;
        return new Promise((resolve, reject) => {
            db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    async transaction(work) {
        await this.run('BEGIN');
        try {
            const result = await work(this);
            await this.run('COMMIT');
            return result;
        } catch (err) {
            await this.run('ROLLBACK');
            throw err;
        }
    }
}

function createConnection(filename = ':memory:') {
    return new Database(filename);
}

module.exports = { createConnection };

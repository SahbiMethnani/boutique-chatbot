import { useState } from 'react';
import { ArrowLeft, CheckCircle2, Database, Download, FileSpreadsheet, Loader2, ShieldCheck, Upload, XCircle } from 'lucide-react';
import './admin.css';

const API_URL = 'http://localhost:8000';
const CSV_TEMPLATE = [
  'nom,description,prix,categorie,tailles,couleurs,stock',
  'Robe ete blanche,Robe legere en coton,89.9,Robes,S|M|L,Blanc,12',
].join('\r\n');

function errorMessage(detail) {
  if (typeof detail === 'string') return detail;
  if (detail?.errors) {
    const errors = detail.errors.map((item) => `Ligne ${item.row} : ${item.error}`);
    if (detail.truncated) errors.push('D’autres erreurs ont été omises.');
    return [detail.message, ...errors].join('\n');
  }
  return detail?.message || 'Échec de l’import.';
}

function Admin() {
  const [adminKey, setAdminKey] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const downloadTemplate = () => {
    const blob = new Blob([`\uFEFF${CSV_TEMPLATE}`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'modele-produits.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || !adminKey.trim()) return;

    setBusy(true);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/admin/import-products-csv`, {
        method: 'POST',
        headers: { 'X-Admin-Key': adminKey },
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(errorMessage(data.detail));
      }
      setResult({ type: 'success', message: data.message });
      setFile(null);
      event.target.reset();
    } catch (error) {
      setResult({ type: 'error', message: error.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="admin-page">
      <header className="admin-header">
        <a className="admin-back" href="/">
          <ArrowLeft size={18} />
          Retour à la boutique
        </a>
        <div className="admin-brand">
          <div className="admin-brand-icon"><ShieldCheck size={24} /></div>
          <div>
            <p className="admin-eyebrow">BOUTIQUE TN</p>
            <h1>Administration</h1>
          </div>
        </div>
      </header>

      <section className="admin-card">
        <div className="admin-card-title">
          <div className="admin-section-icon"><Database size={22} /></div>
          <div>
            <h2>Importer le catalogue</h2>
            <p>Ajoutez plusieurs produits à la base de recherche en une seule fois.</p>
          </div>
        </div>

        <div className="admin-help">
          <FileSpreadsheet size={20} />
          <div>
            <strong>Format du fichier CSV</strong>
            <p>
              Colonnes requises : nom, description, prix, categorie, tailles, couleurs,
              stock. Séparez plusieurs tailles ou couleurs avec le caractère <code>|</code>.
              Les fichiers UTF-8, les séparateurs virgule/point-virgule et les prix décimaux
              avec virgule sont acceptés.
            </p>
            <button type="button" className="admin-template-button" onClick={downloadTemplate}>
              <Download size={16} />
              Télécharger un modèle CSV
            </button>
          </div>
        </div>

        <form className="admin-form" onSubmit={handleSubmit}>
          <label className="admin-label" htmlFor="admin-key">Clé d’administration</label>
          <input
            id="admin-key"
            className="admin-input"
            type="password"
            autoComplete="current-password"
            value={adminKey}
            onChange={(event) => setAdminKey(event.target.value)}
            placeholder="Saisissez la clé configurée dans backend/.env"
            required
          />
          <p className="admin-privacy">
            La clé est envoyée au backend pour cet import et n’est pas enregistrée dans le navigateur.
          </p>

          <label className="admin-label" htmlFor="csv-file">Fichier de produits</label>
          <input
            id="csv-file"
            className="admin-file-input"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null);
              setResult(null);
            }}
            required
          />
          {file && <p className="admin-file-name">{file.name} · {(file.size / 1024).toFixed(1)} Ko</p>}

          {result && (
            <div className={`admin-result ${result.type}`} role="status">
              {result.type === 'success' ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
              <pre>{result.message}</pre>
            </div>
          )}

          <button className="admin-submit" type="submit" disabled={!file || !adminKey.trim() || busy}>
            {busy ? <Loader2 className="admin-spinner" size={19} /> : <Upload size={19} />}
            {busy ? 'Import en cours…' : 'Importer les produits'}
          </button>
        </form>

        <p className="admin-note">
          Tous les produits du fichier sont validés avant l’import. Un produit portant le même nom
          met à jour son entrée existante.
        </p>
      </section>
    </main>
  );
}

export default Admin;

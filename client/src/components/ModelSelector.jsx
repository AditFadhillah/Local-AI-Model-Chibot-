import './ModelSelector.css'

function ModelSelector({ models, selectedModel, onModelChange, loading }) {
  return (
    <div className="model-selector-wrapper">
      <label htmlFor="model-select">Model:</label>
      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={loading || models.length === 0}
        className="model-select"
      >
        {models.length === 0 ? (
          <option>Loading models...</option>
        ) : (
          models.map((model) => (
            <option key={model.name} value={model.name}>
              {model.name}
            </option>
          ))
        )}
      </select>
    </div>
  )
}

export default ModelSelector

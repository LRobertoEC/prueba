document.getElementById('feedback-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        nombre: document.getElementById('nombre').value,
        email: document.getElementById('email').value,
        valoracion: document.querySelector('input[name="valoracion"]:checked')?.value,
        mensaje: document.getElementById('mensaje').value
    };
    
    // Validación básica
    if (!formData.valoracion) {
        alert('Por favor selecciona una valoración');
        return;
    }
    
    fetch('/submit-feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        alert('¡Gracias por tus comentarios!');
        document.getElementById('feedback-form').reset();
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.error || 'Hubo un error al enviar tus comentarios. Por favor intenta nuevamente.');
    });
});
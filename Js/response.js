document.getElementById('contactForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const responseDiv = document.getElementById('responseMessage');
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';
    responseDiv.innerHTML = '';
    
    // Get form data
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        subject: document.getElementById('subject').value,
        message: document.getElementById('message').value
    };
    
    try {
        const response = await fetch('https://d6z0x3xwol.execute-api.eu-north-1.amazonaws.com/prod/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            responseDiv.innerHTML = '<div style="color: green; padding: 10px; border: 1px solid green; background: #d4edda; margin-top: 10px;">' + result.message + '</div>';
            document.getElementById('contactForm').reset();
        } else {
            responseDiv.innerHTML = '<div style="color: red; padding: 10px; border: 1px solid red; background: #f8d7da; margin-top: 10px;">Error: ' + result.message + '</div>';
        }
        
    } catch (error) {
        responseDiv.innerHTML = '<div style="color: red; padding: 10px; border: 1px solid red; background: #f8d7da; margin-top: 10px;">Network error. Please try again.</div>';
    }
    
    // Re-enable button
    submitBtn.disabled = false;
    submitBtn.textContent = 'Send Message';
});
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login - NUCES</title>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; font-family: 'Segoe UI', sans-serif; }

        header {
        background-color: #1a2a6c;
        color: white;
        padding: 25px 50px;
        font-size: 1.8rem;
        font-weight: bold;
        width: 100%;
        box-sizing: border-box;
    }

        .main-container {
        display: flex;
        height: calc(100vh - 85px); /* Adjusted for taller header */
    }
        /* Left Side */
        .left-side {
        flex: 0.7; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 0 5%;
    }

        .left-side h2 { color: #1a2a6c; font-size: 2.2rem; margin-bottom: 5px; }

        .form-group { margin-bottom: 30px; }

        label { display: block; color: #1a2a6c; font-weight: 600; margin-bottom: 10px; }

        input {
            width: 100%; padding: 12px 0; border: none;
            border-bottom: 2px solid #1a2a6c; outline: none; font-size: 1rem;
        }

        .button-container { margin-top: 50px; display: flex; justify-content: center; }

        button {
            padding: 12px 60px; background-color: #1a2a6c; color: white;
            border: none; border-radius: 5px; font-weight: bold; cursor: pointer; transition: 0.3s;
        }

        button:hover { background-color: #e6f0ff; color: #1a2a6c; transform: scale(1.05); }

        .back-link { text-align: center; margin-top: 25px; }
        .back-link a { color: #888; text-decoration: none; font-size: 0.9rem; }

        .right-side {
        flex: 1.3; 
        background: linear-gradient(rgba(26, 42, 108, 0.1), rgba(26, 42, 108, 0.1)),
                    url("{{ url_for('static', filename='background.png') }}");
        background-size: cover;
        /* Changing background-position to 'left' or a percentage 
           shifts the actual content of the photo */
        background-position: 20% center; 
        transition: 0.5s ease;
    }

        .error-msg { color: #e74c3c; margin-bottom: 20px; }
    </style>
</head>
<body>

    <header>National University of Computing and Emerging Sciences</header>

    <div class="main-container">
        <div class="left-side">
            <h2>Login</h2>
            <p style="color: #130f0f; margin-bottom: 40px;">{{ role }} Portal Access</p>

            {% if error %}<p class="error-msg">{{ error }}</p>{% endif %}

            <form action="/auth" method="post">
                <input type="hidden" name="role" value="{{ role }}">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" placeholder="Enter Full Name" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" placeholder="••••••••" required>
                </div>
                <div class="button-container">
                    <button type="submit">SIGN IN</button>
                </div>
                <div class="back-link"><a href="/">← Change Portal</a></div>
            </form>
        </div>
        <div class="right-side"></div>
    </div>

</body>
</html>
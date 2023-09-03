mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"talhayounas0348@gmail.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=true\n\
port = 8000\n\
\n\
[theme]\n\
base = \"dark\"\n\
primaryColor = \"#ffffff\"\n\
backgroundColor = \"#000000\"\n\
secondaryBackgroundColor = \"#040f5f\"\n\
textColor = \"#ffffff\"\n\
font = \"sans serif\"\n\
" > ~/.streamlit/config.toml
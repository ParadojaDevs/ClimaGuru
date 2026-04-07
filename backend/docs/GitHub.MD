# Configurar Git con tu información
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@ejemplo.com"

# Generar clave SSH para GitHub
ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"

# Presiona Enter 3 veces (acepta ubicación por defecto y sin contraseña)

# Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub

# Copia TODO el output (empieza con ssh-ed25519...)


En GitHub.com:

Ve a tu perfil → Settings
SSH and GPG keys → New SSH key
Pega la clave que copiaste
Dale un nombre descriptivo (ej: "VM Ubuntu Backend")
Guarda




Clonar el repositorio:
bash# Ir a tu carpeta home
cd ~

# Clonar el repositorio
git clone git@github.com:xtatikmel/ClimaGuru.git

# Entrar al directorio
cd ClimaGuru

# Verificar que se clonó correctamente
ls -la


 Para colaboradores adicionales
Cada colaborador debe:

Tener acceso al repositorio en GitHub (tú los invitas desde Settings → Collaborators)
Generar su propia clave SSH siguiendo los pasos anteriores
Clonar el repositorio con el mismo comando
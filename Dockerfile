# Build stage
FROM amazon/aws-lambda-python:3.10

RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \ 
    libXcursor libXdamage libXext libXfixes libXi libXrandr libXScrnSaver \
    libXtst pango xorg-x11-server-Xvfb xorg-x11-utils \
    libX11-xcb libxcb libX11 libXau libXdmcp libdr \ 
    xorg-11-xauth dbus-glib dbus-glib-devel  nss mesa-libgbm jq unzip

COPY ./chrome-installer.sh ./chrome-installer.sh 

RUN chmod +x ./chrome-installer.sh 
RUN ./chrome-installer.sh 
RUN rm ./chrome-installer.sh 

RUN pip install --no-cache-dir -r requirements.txt


# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_HOST=gold-prices-scraping.crqscggy6ub7.ap-south-1.rds.amazonaws.com \
    DB_PORT=3306 \
    DB_USER=admin \
    DB_PASSWORD=databasepassword \
    DB_NAME=gold_prices \
    PYTHONPATH=/code

COPY lambda_function.py ./ 

CMD ["lambda_function.lambda_handler"]
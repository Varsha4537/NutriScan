#!/bin/bash
set -e
echo "1. Testing Registration..."
curl -s -c cookies.txt -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Varsha TEST","email":"test@example.com","password":"password123"}'
echo -e "\n\n2. Testing Login..."
curl -s -b cookies.txt -c cookies.txt -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
echo -e "\n\n3. Checking Session (/api/user/me)..."
curl -s -b cookies.txt http://localhost:3000/api/user/me
echo -e "\n\n4. Setting Dietary Profile..."
curl -s -b cookies.txt -X POST http://localhost:3000/api/user/dietary \
  -H "Content-Type: application/json" \
  -d '{"profile":["vegan", "gluten-free"]}'
echo -e "\n\n5. Checking Session again to verify profile..."
curl -s -b cookies.txt http://localhost:3000/api/user/me
echo -e "\n\n6. Testing Food Scan..."
curl -s -b cookies.txt -X POST http://localhost:3000/api/food/scan -F "image=@sample_food.png"
echo -e "\n\n7. Testing Logout..."
curl -s -b cookies.txt -X POST http://localhost:3000/api/auth/logout
echo -e "\n\n8. Checking Session after logout..."
curl -s -b cookies.txt http://localhost:3000/api/user/me

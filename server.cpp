#include "crow.h"

int main() {
    crow::SimpleApp app; // Create the web app

    // Route for home page
    CROW_ROUTE(app, "/")([](){
        return "Welcome to the Smart Waste Management System!";
    });

    // Route for login (POST request)
    CROW_ROUTE(app, "/login").methods("POST"_method)([](const crow::request& req){
        auto body = crow::json::load(req.body);
        if (!body) return crow::response(400);

        std::string username = body["username"].s();
        std::string password = body["password"].s();

        if (username == "admin" && password == "1234") {
            return crow::response(200, "Login Successful!");
        } else {
            return crow::response(403, "Invalid Credentials!");
        }
    });

    // Route for checking bin status
    CROW_ROUTE(app, "/bin_status")([](){
        return "Bin is 70% full";
    });

    // Run the server on port 8080
    app.port(8080).multithreaded().run();
}

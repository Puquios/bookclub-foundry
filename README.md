# BookClub with CF delivery pipeline 

# Try me 
Before you start get API keys for external services.  You will update the secure properties on the Deploy Stage of the generated pipeline.  
* http://developer.nytimes.com
* http://idreambooks.com/api
* http://www.alchemyapi.com

Click this (clones project, creates DevOps Services Project, generates multi-stage pipeline, deploys application to IBM Bluemix):

[![Deploy to Bluemix](https://bluemix.net/deploy/button.png)](https://bluemix.net/deploy?repository=https://github.com/Puquios/bookclub-foundry.git)

# Purpose 
* Demonstrate how to use the IBM Globalization Pipeline Service to dynamically get translated strings.  
* Provide example pipeline for deploying a Cloud Foundry application and dependent services 

# Application 
Forked from [https://hub.jazz.net/pipeline/steveatkin/BookClub](Steve Atkin's BookClub), with additional .bluemix/pipeline.yml file.  

Displays the best sellers information translated into the language you selected.

Java Application running in Liberty.  Binds to the Globalization Pipeline, Watson Machine, and IBM Insights for Twitter as Cloud Foundry Services.  Credentials and endpoints for these services are passed into the application via VCAP_SERVICES environement variable.  In addition leverages APIS from http://developer.nytimes.com, http://idreambooks.com/api and http://www.alchemyapi.com for sources of information about books.  

Contents:   
*   src/main/webapp: This directory contains the client side code (HTML/CSS/JavaScript/Java Server Pages) of the Book Club application.
*   src/main/java: This directory contains the server side code (JAVA) of the Book Club application. 
*   pom.xml: This file builds the Book Club application using Maven

# Pipeline 
[http://robbieminshall.blogspot.com/2015/06/forking-piplines.html](Blog on creation of this pipeline)
* Globalize:  
    - Adds Globalization Pipeline service to the space, binds the application and sends resources for translation where they will be machine translated, and available for review and update from translators.   
* Package application 
    - Executes a maven build which includes static copy of the files
* Deploy 
    - Pushes Cloud Foundry application, if not already in the space creates (free or experimental) instances of Watson Machine Transation, IBM Insights and Globalization.  Passes information about external services as environment variables.  
        



    

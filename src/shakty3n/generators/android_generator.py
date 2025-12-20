"""
Android Application Generator
"""
from typing import Dict
from .base import CodeGenerator


class AndroidAppGenerator(CodeGenerator):
    """Generator for Android applications"""
    
    def __init__(self, ai_provider, output_dir: str, language: str = "kotlin"):
        super().__init__(ai_provider, output_dir)
        self.language = language.lower()
    
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate an Android application project"""
        
        # Generate project structure
        structure = self._generate_structure()
        
        # Generate build.gradle
        build_gradle = self._generate_build_gradle(description, requirements)
        self.create_file("build.gradle", build_gradle)
        
        # Generate app module build.gradle
        app_build_gradle = self._generate_app_build_gradle(description, requirements)
        self.create_file("app/build.gradle", app_build_gradle)
        
        # Generate MainActivity
        main_activity = self._generate_main_activity(description, requirements)
        if self.language == "kotlin":
            self.create_file("app/src/main/java/com/example/app/MainActivity.kt", main_activity)
        else:
            self.create_file("app/src/main/java/com/example/app/MainActivity.java", main_activity)
        
        # Generate AndroidManifest.xml
        manifest = self._generate_manifest(description)
        self.create_file("app/src/main/AndroidManifest.xml", manifest)
        
        # Generate layout
        layout = self._generate_layout(description, requirements)
        self.create_file("app/src/main/res/layout/activity_main.xml", layout)
        
        # Generate README
        readme = self._generate_readme(description)
        self.create_file("README.md", readme)
        
        return {
            "language": self.language,
            "files": self.generated_files,
            "structure": structure
        }
    
    def _generate_structure(self) -> Dict:
        """Create Android project directory structure"""
        dirs = [
            "app/src/main/java/com/example/app",
            "app/src/main/res/layout",
            "app/src/main/res/values",
            "app/src/main/res/drawable",
        ]
        
        for dir_path in dirs:
            self.create_directory(dir_path)
        
        return {"directories": dirs}
    
    def _generate_build_gradle(self, description: str, requirements: Dict) -> str:
        """Generate root build.gradle"""
        return """// Top-level build file
buildscript {
    ext.kotlin_version = '1.9.0'
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.1.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
"""
    
    def _generate_app_build_gradle(self, description: str, requirements: Dict) -> str:
        """Generate app build.gradle"""
        if self.language == "kotlin":
            return """plugins {
    id 'com.android.application'
    id 'kotlin-android'
}

android {
    compileSdk 34
    
    defaultConfig {
        applicationId "com.example.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
    
    kotlinOptions {
        jvmTarget = '1.8'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}
"""
        else:
            return """plugins {
    id 'com.android.application'
}

android {
    compileSdk 34
    
    defaultConfig {
        applicationId "com.example.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}
"""
    
    def _generate_main_activity(self, description: str, requirements: Dict) -> str:
        """Generate MainActivity using AI"""
        prompt = f"""Generate a MainActivity for an Android app.

Language: {self.language.capitalize()}
Description: {description}
Requirements: {requirements}

Generate a complete, functional MainActivity with modern Android best practices.
Return only the code, no explanations."""

        system_prompt = f"You are an expert Android developer. Generate clean, modern {self.language.capitalize()} code."
        
        response = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        # Extract code
        if "```kotlin" in response or "```java" in response:
            start = response.find("```") + 3
            start = response.find("\n", start) + 1
            end = response.find("```", start)
            return response[start:end].strip()
        
        return response.strip()
    
    def _generate_manifest(self, description: str) -> str:
        """Generate AndroidManifest.xml"""
        return """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.app">

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.DarkActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"""
    
    def _generate_layout(self, description: str, requirements: Dict) -> str:
        """Generate activity_main.xml layout"""
        return """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context=".MainActivity">

    <TextView
        android:id="@+id/textView"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Hello Android!"
        android:textSize="24sp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

</androidx.constraintlayout.widget.ConstraintLayout>
"""
    
    def _generate_readme(self, description: str) -> str:
        """Generate README.md"""
        return f"""# Android Application

{description}

## Language
{self.language.capitalize()}

## Requirements
- Android Studio Arctic Fox or newer
- Android SDK 24+
- Gradle 8.1+

## Setup

1. Open project in Android Studio
2. Sync Gradle files
3. Run on emulator or device

## Build

```bash
./gradlew build
```

## Generated by Shakty3n
Autonomous Agentic Coder
"""
